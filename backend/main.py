import re
import json
import logging
from urllib.parse import urlparse
from typing import List, Optional, Literal

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from backend.config import DATA_DIR, KNOWLEDGE_DIR
from backend.groq_service import query_campus_helper

from envi.simulator import CampusSimulator
from core.problem import CampusProblem

from agents.q_learning_agent import QLearningAgent
from algorithms.bfs import BFSAgent
from algorithms.dfs import DFSAgent
from algorithms.greedy_nearest import GreedyNearestAgent
from algorithms.ids import IDSAgent
from algorithms.astar import AStarAgent
from algorithms.ucs import UCSAgent
from algorithms.value_iteration import ValueIterationAgent
from algorithms.simulated_annealing import SimulatedAnnealingAgent


app = FastAPI(title="Campus Saathi API", version="1.0")
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_Q_TABLE_CACHE = {}

def get_trained_q_agent(
    problem: CampusProblem,
    iterations: int = 100
) -> QLearningAgent:
    global _Q_TABLE_CACHE

    agent = QLearningAgent(problem)

    if iterations in _Q_TABLE_CACHE:
        agent.q_table = dict(_Q_TABLE_CACHE[iterations])
        agent.epsilon = (
            0.0 if iterations >= 100
            else max(0.05, 1.0 - (iterations / 75.0))
        )
        agent.name = f"QLearningAgent ({iterations} iter)"
        return agent

    for _ in range(iterations):
        state = ("gate", frozenset())
        done = False
        step_count = 0

        while not done and step_count < 200:
            step_count += 1
            action = agent.select_action(state)

            if not action:
                break

            action_type, target = action
            room, completed = state

            if action_type == "move":
                next_state = (target, completed)
                reward = -2.0
            else:
                next_state = (room, completed | {target})
                reward = 50.0

            done = problem.goal_test(next_state)

            if done:
                reward += 100.0

            agent.update(state, action, reward, next_state, done)
            state = next_state

        agent.decay_epsilon()

    _Q_TABLE_CACHE[iterations] = dict(agent.q_table)

    agent.epsilon = (
        0.0 if iterations >= 100
        else max(0.05, 1.0 - (iterations / 75.0))
    )
    agent.name = f"QLearningAgent ({iterations} iter)"

    return agent


@app.get("/api/map")
def get_campus_map():
    """Returns the campus nodes and edges layout from JSON."""
    try:
        with open(DATA_DIR / "campus_map.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"error": "campus_map.json not found in data directory."}


@app.get("/api/simulate/{agent_type}")
def run_simulation_api(
    agent_type: str,
    congestion: bool = Query(True),
    iterations: int = Query(100),
    start_location: str = Query("gate"),
    completed_steps: list[str] = Query(None),
):
    """Runs a simulation episode for the specified agent type."""
    simulator = CampusSimulator(
        str(DATA_DIR / "campus_map.json"),
        str(DATA_DIR / "steps.json"),
        seed=42,
    )

    is_congestion = congestion if isinstance(congestion, bool) else True
    q_iterations = iterations if isinstance(iterations, int) else 100

    start_room = (
        start_location
        if isinstance(start_location, str)
        and start_location in simulator.graph.nodes
        else "gate"
    )

    valid_completed = (
        completed_steps
        if isinstance(completed_steps, (list, set, tuple, frozenset))
        else None
    )

    completed_fs = (
        frozenset(valid_completed)
        if valid_completed
        else frozenset()
    )

    problem = CampusProblem(
        simulator.graph,
        steps_config=simulator.steps_config,
        start_room=start_room,
    )

    if valid_completed:
        problem.initial_state = lambda: (start_room, completed_fs)

    simulator.problem = problem

    agent_key = agent_type.lower().strip()

    if agent_key.startswith("q_learning"):
        parts = agent_key.replace("-", "_").split("_")

        if len(parts) > 2 and parts[-1].isdigit():
            q_iterations = int(parts[-1])

        agent_key = "q_learning"

    if agent_key == "q_learning":
        agent = get_trained_q_agent(problem, iterations=q_iterations)
    elif agent_key == "a_star":
        agent = AStarAgent(problem)
    elif agent_key == "ucs":
        agent = UCSAgent(problem)
    elif agent_key == "value_iteration":
        agent = ValueIterationAgent(problem)
    elif agent_key == "simulated_annealing":
        agent = SimulatedAnnealingAgent(problem)
    elif agent_key == "bfs":
        agent = BFSAgent(problem)
    elif agent_key == "dfs":
        agent = DFSAgent(problem)
    elif agent_key == "greedy_nearest":
        agent = GreedyNearestAgent(problem)
    elif agent_key == "ids":
        agent = IDSAgent(problem)
    else:
        return {
            "error": (
                f"Agent type '{agent_type}' not supported yet. "
                "Choose from a_star, bfs, dfs, greedy_nearest, ids, "
                "simulated_annealing, q_learning, value_iteration, ucs."
            )
        }

    return simulator.run_simulation(
        agent,
        max_steps=500,
        congestion=is_congestion,
        start_room=start_room,
        completed_steps=completed_fs,
    )

from backend.answering import answer_knowledge_query
from backend.intent_router import classify, get_link_by_key, not_available_text

class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("History message content cannot be empty.")
        return value


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    history: Optional[List[HistoryMessage]] = Field(
        default_factory=list,
        max_length=6,
    )

    @field_validator("query")
    @classmethod
    def validate_query_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Query cannot be empty or whitespace only.")
        return value


class SourceReference(BaseModel):
    id: str
    title: str
    url: str


class ExternalLink(BaseModel):
    label: str
    url: str


class ChatResponse(BaseModel):
    response: str
    found: bool = True
    answer_type: Literal[
        "knowledge",
        "navigation",
        "link",
        "not_available",
    ] = "knowledge"
    sources: List[SourceReference] = Field(default_factory=list)
    links: List[ExternalLink] = Field(default_factory=list)
    node_id: Optional[str] = None
    last_verified: Optional[str] = None



LINK_KEYWORDS = {
    "academic_calendar": [
        "academic calendar",
        "semester calendar",
        "exam date",
        "examination date",
        "vacation",
        "recess",
        "class schedule",
    ],
    "fee_portal": [
        "fee",
        "fees",
        "payment",
        "tuition",
        "fee structure",
    ],
    "notices": [
        "notice",
        "notification",
        "circular",
        "announcement",
    ],
    "admissions": [
        "admission",
        "admissions",
        "reporting",
        "registration",
        "new student",
        "new admission",
    ],
    "student_affairs": [
        "student affairs",
        "dean",
        "counselling",
        "anti-ragging",
        "student office",
    ],
    "library": [
    "library",
    "central library",
    "books",
    "book",
    "reading room",
    "library timings",
    "library hours",
    ],
    "hostel": [
        "hostel",
        "hostels",
        "warden",
        "room allotment",
        "hostel rules",
    ],
    "main_website": [
        "institute website",
        "college website",
        "official website",
    ],
}



def load_knowledge_links() -> List[dict]:
    """Load valid institute links from the knowledge directory."""
    links_file = KNOWLEDGE_DIR / "links.json"

    try:
        with links_file.open("r", encoding="utf-8") as file:
            records = json.load(file)

        if not isinstance(records, list):
            return []

        valid_records = []

        for record in records:
            if not isinstance(record, dict):
                continue

            key = record.get("key")
            label = record.get("label")
            url = record.get("url")

            if not all(isinstance(value, str) and value.strip()
                       for value in (key, label, url)):
                continue

            parsed_url = urlparse(url)

            is_official_domain = (
                parsed_url.hostname == "iiitdmj.ac.in"
                or (
                    parsed_url.hostname is not None
                    and parsed_url.hostname.endswith(".iiitdmj.ac.in")
                )
            )

            if (
                parsed_url.scheme in ("http", "https")
                and is_official_domain
            ):
                valid_records.append(record)

        return valid_records

    except (OSError, json.JSONDecodeError):
        return []


def find_relevant_links(query: str) -> List[ExternalLink]:
    """Find institute links relevant to the user's question."""
    normalized_query = query.lower()
    records = load_knowledge_links()

    relevant_links = []

    for record in records:
        keywords = LINK_KEYWORDS.get(record["key"], [])

        if any(
            re.search(
                rf"\b{re.escape(keyword)}\b",
                normalized_query,
            )
            for keyword in keywords
        ):
            relevant_links.append(
                ExternalLink(
                    label=record["label"],
                    url=record["url"],
                )
            )

    return relevant_links


def find_relevant_sources(query: str) -> List[SourceReference]:
    """Return verified source references relevant to the user's question."""
    normalized_query = query.lower()
    records = load_knowledge_links()

    relevant_sources = []

    for record in records:
        keywords = LINK_KEYWORDS.get(record["key"], [])

        if any(
            re.search(
                rf"\b{re.escape(keyword)}\b",
                normalized_query,
            )
            for keyword in keywords
        ):
            source_url = record.get("url")

            if not source_url:
                continue

            relevant_sources.append(
                SourceReference(
                    id=record["key"],
                    title=record["label"],
                    url=source_url,
                )
            )

    return relevant_sources



@app.post("/api/chat", response_model=ChatResponse)
def chat_campus_helper(request: ChatRequest):

    def simulation_callback(
        agent_type: str,
        congestion: bool = True,
        start_location: str = "gate",
        completed_steps: list = None,
    ):
        return run_simulation_api(
            agent_type=agent_type,
            congestion=congestion,
            iterations=100,
            start_location=start_location,
            completed_steps=completed_steps,
        )

    intent = classify(request.query)

    if intent == "greeting":
        return ChatResponse(
            response="Hello! How can I help you with the campus?",
            found=True,
            answer_type="knowledge",
        )

    if intent == "link":
        query_lower = request.query.lower()

        link_key = (
            "timetable"
            if "timetable" in query_lower or "time table" in query_lower
            else "academic_calendar"
        )

        link = get_link_by_key(link_key)

        if link and link.get("url"):
            url = link["url"]

            return ChatResponse(
                response=f"You can find the requested information here: {url}",
                found=True,
                answer_type="link",
                links=[
                    ExternalLink(
                        label=link.get("label", link_key),
                        url=url,
                    )
                ],
                sources=find_relevant_sources(request.query),
                node_id=link.get("node_id"),
                last_verified=link.get("last_verified"),
            )

        response, main_url = not_available_text(
            get_link_by_key("main_website")
        )

        return ChatResponse(
            response=response,
            found=False,
            answer_type="not_available",
            links=[
                ExternalLink(
                    label="IIITDM Jabalpur Website",
                    url=main_url,
                )
            ],
        )

    if intent == "navigation":
        try:
            reply = query_campus_helper(
                request.query,
                simulation_callback,
            )

            return ChatResponse(
                response=reply,
                found=True,
                answer_type="navigation",
                sources=find_relevant_sources(request.query),
            )

        except Exception:
            logger.exception("Navigation chat request failed")
            response, main_url = not_available_text(
                get_link_by_key("main_website")
            )

            return ChatResponse(
                response=response,
                found=False,
                answer_type="not_available",
                links=[
                    ExternalLink(
                        label="IIITDM Jabalpur Website",
                        url=main_url,
                    )
                ],
            )

    try:
        result = answer_knowledge_query(
            request.query,
            history=[
                message.model_dump()
                for message in (request.history or [])
            ],
        )

        links = [
            ExternalLink(
                label="Official source",
                url=url,
            )
            for url in result.links
        ]

        return ChatResponse(
            response=result.answer,
            found=result.found,
            answer_type=(
                "knowledge" if result.found else "not_available"
            ),
            sources=find_relevant_sources(request.query),
            links=links,
        )

    except Exception:
        logger.exception("Knowledge chat request failed")
        response, main_url = not_available_text(
            get_link_by_key("main_website")
        )

        return ChatResponse(
            response=response,
            found=False,
            answer_type="not_available",
            links=[
                ExternalLink(
                    label="IIITDM Jabalpur Website",
                    url=main_url,
                )
            ],
        )

