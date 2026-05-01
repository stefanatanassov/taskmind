from __future__ import annotations

from taskmind.agents.registry import AgentRegistry


def test_registry_loads_rich_agent_contracts():
    registry = AgentRegistry(config_dir="config/agents")
    agents = registry.list_agents()

    assert len(agents) == 3
    assert any(agent.role == "planner" for agent in agents)

    planner = next(agent for agent in agents if agent.role == "planner")
    assert planner.purpose
    assert planner.material_refs
    assert planner.material_refs[0].path == "docs/materials/planning-principles.md"


def test_registry_filters_active_role():
    registry = AgentRegistry(config_dir="config/agents")
    critics = registry.get_agents_for_role("critic")

    assert len(critics) == 1
    assert critics[0].name == "Critic"
