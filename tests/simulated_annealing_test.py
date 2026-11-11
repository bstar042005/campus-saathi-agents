import itertools

import numpy as np
import pytest

from agents.base_agent import BaseAgent
from algorithms.simulated_annealing import SimulatedAnnealingAgent, optimal_order, travel_cost
from core.problem import CampusProblem
from envi.simulator import CampusSimulator


@pytest.fixture(scope="module")
def problem():
    simulator = CampusSimulator("data/campus_map.json", "data/steps.json", seed=42)
    return CampusProblem(simulator.graph, simulator.steps_config)


@pytest.fixture
def agent(problem):
    return SimulatedAnnealingAgent(problem)


def test_agent_is_a_base_agent(agent):
    assert isinstance(agent, BaseAgent)


def test_optimal_order_matches_brute_force(agent):
    rooms = ["lhtc_gate", "L-103", "L-106", "panini_gate", "shop", "room"]
    brute = min(travel_cost(agent.dist, "gate", p) for p in itertools.permutations(rooms))
    order, cost = optimal_order(agent.dist, "gate", rooms)
    assert cost == brute
    assert travel_cost(agent.dist, "gate", order) == cost
    assert sorted(order) == sorted(rooms)


def test_optimal_order_small_inputs(agent):
    assert optimal_order(agent.dist, "gate", []) == ([], 0.0)
    assert optimal_order(agent.dist, "gate", ["shop"]) == (["shop"], agent.dist["gate"]["shop"])


def test_neighbours_keep_the_same_rooms(agent):
    rng = np.random.default_rng(3)
    order = sorted(agent.problem.steps_config)
    for _ in range(200):
        assert sorted(agent._neighbour(order, rng)) == order


def test_both_swap_and_insert_moves_happen(agent):
    rng = np.random.default_rng(3)
    order = sorted(agent.problem.steps_config)
    changed = set()
    for _ in range(500):
        candidate = agent._neighbour(order, rng)
        changed.add(sum(a != b for a, b in zip(order, candidate)))
    assert 2 in changed
    assert any(count > 2 for count in changed)


def test_exponential_schedule_shrinks_towards_min(problem):
    agent = SimulatedAnnealingAgent(problem, initial_temp=10.0, cooling_rate=0.9, min_temp=0.5)
    temps = list(agent.temperatures())
    assert temps[0] == 10.0
    assert all(a > b for a, b in zip(temps, temps[1:]))
    assert all(t > 0.5 for t in temps)
    assert temps[-1] * 0.9 <= 0.5


def test_linear_schedule_drops_evenly(problem):
    agent = SimulatedAnnealingAgent(problem, schedule="linear", initial_temp=10.0, cooling_rate=0.9, min_temp=0.5)
    temps = list(agent.temperatures())
    assert np.allclose(np.diff(temps), -1.0)
    assert temps[0] == 10.0
    assert all(t > 0.5 for t in temps)


@pytest.mark.parametrize("kwargs", [
    {"schedule": "cosine"},
    {"cooling_rate": 1.0},
    {"cooling_rate": 0.0},
    {"min_temp": 100.0},
    {"restarts": 0},
])
def test_bad_parameters_are_rejected(problem, kwargs):
    with pytest.raises(ValueError):
        SimulatedAnnealingAgent(problem, **kwargs)


def test_same_seed_gives_same_result(problem):
    rooms = sorted(problem.steps_config)
    first = SimulatedAnnealingAgent(problem, seed=11)
    second = SimulatedAnnealingAgent(problem, seed=11)
    assert first.anneal("gate", rooms) == second.anneal("gate", rooms)
    assert first.trace == second.trace


@pytest.mark.parametrize("schedule", ["exponential", "linear"])
def test_parameters_change_the_search(problem, schedule):
    rooms = sorted(problem.steps_config)
    short = SimulatedAnnealingAgent(problem, schedule=schedule, restarts=1, cooling_rate=0.9)
    long = SimulatedAnnealingAgent(problem, schedule=schedule, restarts=2, cooling_rate=0.99)
    short.anneal("gate", rooms)
    long.anneal("gate", rooms)
    assert len(long.trace) > len(short.trace)


def test_default_settings_find_the_optimum(problem):
    rooms = sorted(problem.steps_config)
    _, best = optimal_order(SimulatedAnnealingAgent(problem).dist, "gate", rooms)
    for seed in range(10):
        _, cost = SimulatedAnnealingAgent(problem, seed=seed).anneal("gate", rooms)
        assert cost == best


def test_more_restarts_never_hurt(problem):
    rooms = sorted(problem.steps_config)
    for seed in range(10):
        one = SimulatedAnnealingAgent(problem, restarts=1, seed=seed).anneal("gate", rooms)[1]
        five = SimulatedAnnealingAgent(problem, restarts=5, seed=seed).anneal("gate", rooms)[1]
        assert five <= one


def test_trace_never_gets_worse(agent):
    agent.anneal("gate", sorted(agent.problem.steps_config))
    assert all(a >= b for a, b in zip(agent.trace, agent.trace[1:]))


def test_goal_state_returns_no_action(problem, agent):
    assert agent.select_action(("shop", frozenset(problem.steps_config))) is None


def test_actions_are_legal_and_reach_goal(problem, agent):
    state = problem.initial_state()
    for _ in range(100):
        action = agent.select_action(state)
        if action is None:
            break
        assert action in problem.actions(state)
        state = problem.result(state, action)
    assert problem.goal_test(state)


def test_agent_replans_when_progress_differs_from_plan(problem, agent):
    agent.select_action(problem.initial_state())
    odd_state = ("L-103", frozenset({"gate", "shop"}))
    action = agent.select_action(odd_state)
    assert action in problem.actions(odd_state)
    assert len(agent.plan) == len(problem.steps_config) - 2


def test_reset_clears_the_plan(problem, agent):
    agent.select_action(problem.initial_state())
    agent.reset()
    assert agent.plan is None and agent.plan_cost is None


def test_simulator_travel_matches_the_plan(problem, agent):
    simulator = CampusSimulator("data/campus_map.json", "data/steps.json", seed=42)
    summary = simulator.run_simulation(agent, max_steps=500)
    full_service = sum(cfg["mean_service_time"] for cfg in simulator.steps_config.values())
    assert summary["metrics"]["travel_time"] == agent.plan_cost
    assert summary["metrics"]["service_time"] == full_service
