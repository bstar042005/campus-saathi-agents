# Campus Saathi Agents

A multi-agent campus reporting simulator that helps a first-time student complete reporting formalities across an academic and hostel campus. It models campus navigation, service times, queues, and crowd congestion, then compares multiple AI and search-based agents to determine how they complete the reporting journey.

The project includes a simulation engine, nine planning/search agents, a FastAPI backend, a React dashboard, and an LLM-powered campus assistant.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [How the Simulation Works](#how-the-simulation-works)
- [Algorithms and Agents](#algorithms-and-agents)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Set Up the Backend](#2-set-up-the-backend)
  - [3. Set Up the Frontend](#3-set-up-the-frontend)
- [Environment Variables](#environment-variables)
- [Using the Application](#using-the-application)
- [Backend API](#backend-api)
- [Chat Assistant](#chat-assistant)
- [Running Tests](#running-tests)
- [Experiments](#experiments)
- [Configuration and Customization](#configuration-and-customization)
- [Documentation](#documentation)

---

## Overview

A newly admitted student may need to visit several rooms and offices to complete campus reporting formalities. The order of visits matters: some rooms are far apart, some formalities take longer, and queues can increase waiting time.

Campus Saathi models this problem as a search and planning task. Different agents are placed in the same simulated campus environment and evaluated on the time and cost required to complete all required steps.

The objective is to minimize:

**Total Cost = Travel Time + Queue Waiting Time + Service Time**

The dashboard makes the agents' routes and performance metrics easier to compare.

## Key Features

- **Multi-agent simulation:** Compare nine agents using different search, optimization, planning, and reinforcement-learning approaches.
- **Campus graph:** Represent campus locations as nodes connected by weighted travel paths.
- **Queue and crowd simulation:** Model FIFO queues, parallel service counters, and background students.
- **Performance metrics:** Track travel time, waiting time, service time, total cost, and simulation steps.
- **Interactive dashboard:** View the campus map, follow agent routes, and compare simulation results.
- **AI campus assistant:** Ask where to go next using a Groq-powered language model connected to simulation tools.
- **Configurable campus data:** Update locations, routes, reporting steps, and service information through JSON files.
- **Reproducible experiments:** Use seeded simulations and evaluation scripts to compare approaches.

## How the Simulation Works

### 1. Campus environment

The campus is represented as a weighted graph containing locations in two main clusters:

| Area | Locations |
|---|---|
| Neutral | `gate` |
| Academic | `lhtc_gate`, `L-103`, `L-104`, `L-105`, `L-106`, `L-206` |
| Hostel | `panini_gate`, `office`, `room`, `shop` |

Edges represent paths between locations, and their weights represent travel costs or time. Moving between the academic and hostel clusters can be more expensive than moving within a cluster.

The campus layout is defined in `data/campus_map.json`.

### 2. Reporting steps

Each reporting step is associated with a campus location and has service-time and counter information. These details are stored in `data/steps.json`.

### 3. Agent state and actions

The planning problem uses a state of the form:

`(current_room, frozenset(completed_steps))`

An agent can take actions such as:

- `("move", neighbour)` — move to a connected location.
- `("complete", current_room)` — complete the reporting step at the current location.

The goal is to complete every required reporting step.

### 4. Queue and congestion model

The simulator models queues using FIFO room counters with multiple parallel service counters. Background students move through the campus and join queues, affecting the waiting time experienced by the evaluated agent.

Congestion can be enabled or disabled:

- **Congestion enabled:** Includes queue waiting and background student activity.
- **Congestion disabled:** Helps compare route and service costs without queue effects.

A seed is used to make simulations reproducible.

## Algorithms and Agents

The project implements nine agents:

| Agent | Approach | Description |
|---|---|---|
| BFS | Uninformed search | Explores the state space breadth-first. |
| DFS | Uninformed search | Explores one branch deeply before backtracking. |
| IDS | Uninformed search | Repeats depth-limited search with increasing depth limits. |
| UCS | Cost-based search | Expands the lowest accumulated-cost state first. |
| A* | Informed search | Combines path cost with an admissible heuristic. |
| Greedy Nearest | Heuristic | Visits the nearest unfinished reporting location. |
| Simulated Annealing | Local search | Optimizes the order in which reporting locations are visited. |
| Value Iteration | MDP planning | Computes a policy using rewards and state-transition probabilities. |
| Q-Learning | Reinforcement learning | Learns a policy through interaction with the simulator. |

Implementation files are located in `algorithms/` and `agents/`. Each agent follows the common interface defined in `agents/base_agent.py`.

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, Vite, JavaScript, CSS |
| Backend | Python, FastAPI, Uvicorn |
| AI assistant | Groq API, tool-based simulation calls |
| Search and planning | BFS, DFS, IDS, UCS, A*, Greedy Search, Simulated Annealing, Value Iteration |
| Reinforcement learning | Tabular Q-Learning |
| Simulation and data | Python, JSON, NumPy |
| Testing | pytest |
| Retrieval / knowledge search | rank-bm25 |

## Project Structure

```text
campus-saathi-agents/
│
├── agents/
│   ├── base_agent.py
│   └── q_learning_agent.py
│
├── algorithms/
│   ├── astar.py
│   ├── bfs.py
│   ├── dfs.py
│   ├── greedy_nearest.py
│   ├── heuristics.py
│   ├── ids.py
│   ├── simulated_annealing.py
│   ├── ucs.py
│   └── value_iteration.py
│
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── groq_service.py
│   ├── intent_router.py
│   ├── answering.py
│   ├── knowledge.py
│   └── .env.example
│
├── core/
│   ├── problem.py
│   ├── counters.py
│   ├── metrics.py
│   └── seeding.py
│
├── data/
│   ├── campus_map.json
│   ├── steps.json
│   └── knowledge/
│
├── docs/
│   ├── PROBLEM.md
│   ├── PEAS.md
│   ├── ENVIRONMENT.md
│   └── algorithms/
│
├── envi/
│   ├── campus_graph.py
│   └── simulator.py
│
├── experiments/
│   ├── eval_simulated_annealing.py
│   ├── eval_value_iteration.py
│   └── train_q.py
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── .env.example
│
├── scripts/
├── tests/
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

Install the following before running the project:

- Python 3.10 or later
- Node.js 18 or later and npm
- Git
- A Groq API key (only required for the AI chat assistant)

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd campus-saathi-agents
```

### 2. Set Up the Backend

Create and activate a virtual environment from the project root.

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Create the backend environment file:

**Windows (PowerShell):**

```powershell
Copy-Item backend/.env.example backend/.env
```

**macOS / Linux:**

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and add your Groq API key if you want to use the chat assistant.

Start the API server from the **repository root**:

```bash
uvicorn backend.main:app --reload --port 8000
```

The backend will be available at:

- API base URL: `http://127.0.0.1:8000`
- Interactive API documentation: `http://127.0.0.1:8000/docs`

### 3. Set Up the Frontend

Open a second terminal:

```bash
cd frontend
npm install
```

Create the frontend environment file:

**Windows (PowerShell):**

```powershell
Copy-Item .env.example .env
```

**macOS / Linux:**

```bash
cp .env.example .env
```

The example configuration points to the local backend:

```env
VITE_API_URL=http://127.0.0.1:8000
```

Start the frontend development server:

```bash
npm run dev
```

Open the local URL printed by Vite in your terminal (commonly `http://localhost:5173`).

> Keep the backend and frontend terminals running while using the application.

## Environment Variables

### Backend — `backend/.env`

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | API key used by the Groq-powered chat assistant. |
| `GROQ_MODEL` | Groq model identifier used for chat completions. |
| `CORS_ORIGINS` | Allowed frontend origins. |

Example:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=qwen/qwen3.8-27b
CORS_ORIGINS=http://localhost:5173
```

### Frontend — `frontend/.env`

| Variable | Purpose |
|---|---|
| `VITE_API_URL` | Base URL of the FastAPI backend. |

Example:

```env
VITE_API_URL=http://127.0.0.1:8000
```

Never commit real API keys or secret environment files to version control.

## Using the Application

1. Start the backend and frontend.
2. Open the frontend in your browser.
3. Select an agent or compare the available simulation results using the dashboard.
4. Inspect the route on the campus map.
5. Compare travel, waiting, service, and total-cost metrics.
6. Use the chat assistant to ask for guidance about the next reporting step.

The exact controls and layout are provided by the frontend interface.

## Backend API

The FastAPI backend exposes endpoints for campus data, simulations, and chat.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/map` | Returns campus nodes and edges. |
| `GET` | `/api/simulate/{agent_type}` | Runs a simulation for the selected agent. |
| `POST` | `/api/chat` | Sends a question to the AI campus assistant. |

### Run a simulation

Example: run A* with congestion enabled.

```bash
curl "http://127.0.0.1:8000/api/simulate/a_star?congestion=true"
```

Supported agent identifiers:

```text
a_star
ucs
bfs
dfs
ids
greedy_nearest
simulated_annealing
value_iteration
q_learning
```

The Q-Learning endpoint also accepts an iteration count in the agent identifier (for example, `q_learning_500`) or through the supported query parameter.

The simulation endpoint supports parameters such as:

| Parameter | Default | Description |
|---|---|---|
| `congestion` | `true` | Enables or disables queue and crowd effects. |
| `iterations` | `100` | Q-Learning training episodes. |
| `start_location` | `gate` | Starting campus location. |
| `completed_steps` | None | Repeatable parameter for steps already completed. |

Example with a custom start location and completed steps:

```bash
curl "http://127.0.0.1:8000/api/simulate/q_learning?iterations=500&start_location=L-103&completed_steps=gate&completed_steps=lhtc_gate"
```

A simulation response contains the selected agent, number of steps, performance metrics, and a trace of the agent's actions. Depending on the response, background-student positions may also be included.

Example response shape:

```json
{
  "agent": "AStarAgent",
  "total_steps": 42,
  "metrics": {
    "travel_time": 0,
    "wait_time": 0,
    "service_time": 0,
    "total_cost": 0
  },
  "trace": [
    {
      "step": 1,
      "current_room": "gate",
      "completed_steps": ["gate"],
      "action_taken": ["complete", "gate"]
    }
  ],
  "background_steps": []
}
```

The numeric values above are illustrative; actual values depend on the selected agent, configuration, and simulation seed.

## Chat Assistant

The chat endpoint connects a Groq-hosted language model to the campus knowledge base and simulation tools.

The assistant can interpret a student's current location and already-completed reporting steps, request route calculations from the simulator, and respond with route guidance and the next recommended action.

Example question:

```text
I'm at L-104 and have finished the gate and allotment verification.
What should I do next?
```

To enable chat:

1. Obtain an API key from Groq.
2. Add it to `GROQ_API_KEY` in `backend/.env`.
3. Set `GROQ_MODEL` to a model available to your Groq account.
4. Restart the backend.

The simulation endpoints can be used independently of the Groq chat integration.

## Running Tests

Run tests from the repository root with the virtual environment activated:

```bash
python -m pytest
```

To run a specific test file:

```bash
python -m pytest tests/test_astar.py
```

## Experiments

The `experiments/` directory contains scripts for evaluating and training selected algorithms.

Run them from the repository root:

```bash
python -m experiments.eval_simulated_annealing
python -m experiments.eval_value_iteration
python -m experiments.train_q
```

These scripts can be used to study optimization quality, planning performance, and Q-Learning behavior under the configured simulation environment.

## Configuration and Customization

You can adapt the simulation to a different campus without changing the core algorithms:

- **Campus layout:** Edit `data/campus_map.json` to change locations and weighted connections.
- **Reporting requirements:** Edit `data/steps.json` to change the steps, their locations, and service configuration.
- **Campus assistant knowledge:** Update the JSON files in `data/knowledge/` using the structure described in `data/knowledge/SCHEMA.md`.
- **Frontend API URL:** Change `VITE_API_URL` in `frontend/.env` when the backend runs at a different address.
- **Backend CORS:** Update `CORS_ORIGINS` in `backend/.env` to match the frontend origin.

After changing configuration data, restart the backend so it reloads the updated files.

## Documentation

Additional technical documentation is available in `docs/`:

- `docs/PROBLEM.md` — problem formulation.
- `docs/PEAS.md` — PEAS description of the agent environment.
- `docs/ENVIRONMENT.md` — environment and simulation details.
- `docs/CHAT_API.md` — chat API information.
- `docs/CONVENTIONS.md` — project conventions.
- `docs/algorithms/` and `algorithms/` — algorithm-specific explanations and implementation notes.

---

## License

See [LICENSE](LICENSE) for license information.
