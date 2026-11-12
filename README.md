multi-agent campus reporting simulator. A first-time student must complete a checklist of reporting steps spread across a campus (academic block + hostel block), and different AI agents — classical search, local search, an MDP planner, and a reinforcement-learning agent — compete to finish in the least total time under queueing congestion.

The project ships with:

a simulation engine (campus graph, FIFO room counters, a scripted crowd of background students),
9 agents (BFS, DFS, IDS, UCS, A*, Greedy Nearest, Simulated Annealing, Value Iteration, Q-Learning),
a FastAPI backend that runs simulations and exposes a chatbot,
a React dashboard that animates each agent's route on the campus map and compares metrics,
an LLM chat assistant (Groq) that runs the simulations as tools and tells a student where to go next.
The problem

A student arrives at the gate and must complete every reporting step on campus. Each step happens in a specific room and costs time:

Total time = travel time + queue waiting time + service time

The campus is a weighted graph of 11 nodes in two clusters, joined by costly crossing edges:

Cluster	Rooms
Neutral	gate
Academic	lhtc_gate, L-103, L-104, L-105, L-106, L-206
Hostel	panini_gate, office, room, shop

Each room has a step (e.g. Fee Clearance & Accounts at L-104, Warden Clearance at office), a mean service time and a number of counters. These live in data/campus_map.json and data/steps.json, so the campus can be changed without touching code.

State: (current_room, frozenset(completed_steps)) Actions: ("move", neighbour) or ("complete", current_room) Goal: every step in steps.json is completed Cost: sum of edge travel times + service times + queue waits

Formal write-ups are in docs/: PROBLEM.md, PEAS.md, ENVIRONMENT.md.

Agents
Agent	Family	File	Notes
BFS	Uninformed search	algorithms/bfs.py	
DFS	Uninformed search	algorithms/dfs.py	
IDS	Uninformed search	algorithms/ids.py	Iterative deepening
UCS	Uninformed, cost-aware	algorithms/ucs.py	A* with h = 0
A*	Informed search	algorithms/astar.py	Admissible + consistent heuristics in heuristics.py (farthest-remaining-room, cluster-aware). See algorithms/astar.md for proofs
Greedy Nearest	Heuristic	algorithms/greedy_nearest.py	Always goes to the nearest unfinished room (Dijkstra)
Simulated Annealing	Local search	algorithms/simulated_annealing.py	Optimises visiting order; exact Held-Karp optimum used as a reference. See docs/algorithms/simulated_annealing.md
Value Iteration	MDP planning	algorithms/value_iteration.py	State includes a low/medium/high congestion level (67,584 states). See docs/algorithms/value_iteration.md
Q-Learning	Reinforcement learning	agents/q_learning_agent.py	Epsilon-greedy, tabular; trained online against the simulator

All agents extend BaseAgent (agents/base_agent.py) and implement select_action(state, metrics).

How the simulator models congestion

envi/simulator.py runs one episode for an agent and returns a step-by-step trace plus metrics.

Every room with a step has a RoomCounter (core/counters.py): a FIFO queue served by num_counters parallel counters, with gamma-distributed service times.
20 background students wander the campus on shortest paths and join queues, so congestion is stochastic but reproducible (seeded; the API uses seed=42).
When the agent completes a step with congestion on, it waits roughly in proportion to the queue length / crowd in that room and the room's mean service time.
Congestion can be switched off to compare agents on pure travel + service cost.
Project structure
.
├── agents/            BaseAgent + Q-learning agent
├── algorithms/        BFS, DFS, IDS, UCS, A*, Greedy, Simulated Annealing, Value Iteration, heuristics
├── core/              CampusProblem (formulation), RoomCounter (queues), MetricsTracker, seeding
├── envi/              CampusGraph + CampusSimulator
├── data/              campus_map.json, steps.json
├── backend/           FastAPI app (main.py) + Groq chat service (groq_service.py)
├── frontend/          React + Vite dashboard
├── experiments/       Training / evaluation scripts
├── tests/             pytest suite
└── docs/              Problem formulation, PEAS, environment, algorithm write-ups
Getting started
Prerequisites
Python 3.10+ (the code uses list[str] type hints)
Node.js 18+ and npm (for the dashboard)
A Groq API key (only needed for the chat assistant)
1. Backend

From the repository root (the backend reads data/*.json using relative paths):

bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp backend/.env.example backend/.env
# edit backend/.env and set GROQ_API_KEY=<your key>

uvicorn backend.main:app --reload --port 8000

The API is now at http://127.0.0.1:8000 (interactive docs at /docs).

2. Frontend
bash
cd frontend
npm install
npm run dev

Open the URL Vite prints (usually http://localhost:5173). The frontend expects the backend at http://127.0.0.1:8000.

API
Method	Endpoint	Description
GET	/api/map	Campus nodes and edges
GET	/api/simulate/{agent_type}	Run one episode and return the trace and metrics
POST	/api/chat	Ask the LLM assistant; body: {"query": "..."}

/api/simulate/{agent_type}

agent_type: a_star, ucs, bfs, dfs, ids, greedy_nearest, simulated_annealing, value_iteration, q_learning (also q_learning_<iterations>).

Query param	Default	Meaning
congestion	true	Enable queues and background students
iterations	100	Q-learning training episodes
start_location	gate	Room to start from
completed_steps	none	Repeatable; steps already done
bash
curl "http://127.0.0.1:8000/api/simulate/a_star?congestion=true"
curl "http://127.0.0.1:8000/api/simulate/q_learning?iterations=500&start_location=L-103&completed_steps=gate&completed_steps=lhtc_gate"

Response shape:

jsonc
{
  "agent": "AStarAgent",
  "total_steps": 42,
  "metrics": { "travel_time": 0, "wait_time": 0, "service_time": 0, "total_cost": 0 },
  "trace": [
    { "step": 1, "current_room": "gate", "completed_steps": ["gate"], "action_taken": ["complete", "gate"] }
  ],
  "background_steps": [ [ { "id": "student_1", "current_room": "L-104" } ] ]
}

Q-learning agents are trained on request and cached per iteration count, so the first call with a new iterations value is slower.

Chat assistant

POST /api/chat sends the student's message to a Groq-hosted LLM with two tools, simulate_all_paths and simulate_path, which call the simulator. The model extracts the student's current location and completed steps from the message, runs the algorithms, picks the cheapest route, and replies with just the route and the immediate next step.

Example prompts: "I'm at L-104 and have finished the gate and allotment verification — what next?"

Notes:

The model name is set in backend/groq_service.py; change it there if your Groq account uses a different one.
The chat tools currently cover a_star, bfs, dfs, greedy_nearest and q_learning only.
Tests and experiments
bash
pip install pytest
python -m pytest

Experiments (run from the repo root):

bash
python -m experiments.eval_simulated_annealing   # cooling schedules vs. exact Held-Karp optimum
python -m experiments.eval_value_iteration       # value iteration vs. a nearest-room baseline
python -m experiments.train_q                    # Q-learning learning curve at episode milestones
Known issues
CampusSimulator.run_simulation returns metrics nested under "metrics", but a few older callers still read them from the top level. As a result tests/simulated_annealing_test.py::test_simulator_travel_matches_the_plan and tests/value_iteration_test.py::test_policy_completes_every_step_in_simulator fail, and experiments/train_q.py and experiments/eval_value_iteration.py crash with a KeyError / TypeError. The fix is to read result["metrics"][...].
The frontend hardcodes http://127.0.0.1:8000; change it in App.jsx, CampusMap.jsx and ChatModal.jsx if you deploy the backend elsewhere.
CORS is open to all origins (allow_origins=["*"]), which is fine for local development but should be restricted in production.
docs/PROBLEM.md mentions 10 reporting steps, but data/steps.json defines 11 (including the gate step), and the goal test uses all of them.
