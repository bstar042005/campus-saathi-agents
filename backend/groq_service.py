import os
import json
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from backend.config import GROQ_MODEL

CURRENT_DIR = Path(__file__).resolve().parent
ENV_PATH = CURRENT_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

ALGORITHMS = ["a_star", "bfs", "dfs", "greedy_nearest", "q_learning"]

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "simulate_all_paths",
            "description": "Run simulations across all available pathfinding algorithms (a_star, bfs, dfs, greedy_nearest, q_learning) and return their respective metrics and trajectories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "current_location": {
                        "type": "string",
                        "description": "User current location or starting room (defaults to 'gate')."
                    },
                    "completed_steps": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Rooms already completed (defaults to ['gate'])."
                    },
                    "congestion": {
                        "type": "boolean",
                        "description": "Whether to consider dynamic congestion (default true)."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "simulate_path",
            "description": "Run simulation for a single specific pathfinding algorithm.",
            "parameters": {
                "type": "object",
                "properties": {
                    "algorithm": {
                        "type": "string",
                        "enum": ["a_star", "bfs", "dfs", "greedy_nearest", "q_learning"],
                        "description": "The pathfinding algorithm to simulate."
                    },
                    "current_location": {
                        "type": "string",
                        "description": "User current location or starting room (defaults to 'gate')."
                    },
                    "completed_steps": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Rooms already completed (defaults to ['gate'])."
                    },
                    "congestion": {
                        "type": "boolean",
                        "description": "Whether to consider dynamic congestion (default true)."
                    }
                },
                "required": ["algorithm"]
            }
        }
    }
]

SYSTEM_PROMPT = """You are Campus Saathi, an intelligent multi-agent campus pathfinding assistant.
Your goal is to guide students and visitors through campus procedures along the most optimal path.

Instructions:
1. Extract the user's current location and completed steps from their query.
2. Fallback logic: If no start location is specified, assume "gate". If a location is specified, use it. Always assume "gate" as completed by default if no completed steps are provided.
3. Call simulate_all_paths (or simulate_path across all algorithms) to fetch the pathfinding metrics.
4. Internally evaluate all algorithm results to select the optimal path having the lowest total cost and travel time.
5. In your final response, provide ONLY:
    - The optimal path (route sequence of locations to visit).
    - The immediate next step the user must take right now.
    Strictly do NOT mention algorithm names (such as A*, Greedy, BFS, DFS, Q-Learning) or numerical metrics (travel time, wait time, cost, steps) unless the user explicitly asks for them."""

def query_campus_helper(user_query: str, run_simulation_callback):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query}
    ]

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto"
    )

    response_message = response.choices[0].message
    messages.append(response_message)

    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            function_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
            congestion = function_args.get("congestion", True)
            location = function_args.get("current_location", "gate")
            completed = function_args.get("completed_steps", ["gate"])

            def summarize_sim(res):
                if not isinstance(res, dict):
                    return res
                trace = res.get("trace", [])
                completed_sequence = [s["current_room"] for s in trace if s.get("action_taken", [None])[0] == "complete"]
                full_moves = [s["current_room"] for s in trace if s.get("action_taken", [None])[0] == "move"]
                return {
                    "agent": res.get("agent"),
                    "total_steps": res.get("total_steps"),
                    "metrics": res.get("metrics"),
                    "route": full_moves,
                    "completed_sequence": completed_sequence
                }

            if tool_call.function.name == "simulate_all_paths":
                sim_result = {}
                for algo in ALGORITHMS:
                    raw_res = run_simulation_callback(
                        agent_type=algo,
                        congestion=congestion,
                        start_location=location,
                        completed_steps=completed
                    )
                    sim_result[algo] = summarize_sim(raw_res)
            else:
                algo = function_args.get("algorithm", "a_star")
                raw_res = run_simulation_callback(
                    agent_type=algo,
                    congestion=congestion,
                    start_location=location,
                    completed_steps=completed
                )
                sim_result = summarize_sim(raw_res)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "content": json.dumps(sim_result)
            })

        final_response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=messages
        )
        return final_response.choices[0].message.content

    return response_message.content

def generate_structured_rag_response(
    system_prompt: str,
    user_message: str,
    history: list[dict] | None = None,
    temperature: float = 0.1,
) -> str:
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content or ""