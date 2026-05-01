from __future__ import annotations

from pathlib import Path

import yaml

from taskmind.agents.schemas import AgentContract, AgentRuntimeProfile
from taskmind.config import get_settings
from taskmind.providers.base import ReferenceMaterial

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class AgentRegistry:
    def __init__(self, config_dir: str | None = None) -> None:
        settings = get_settings()
        self.config_dir = Path(config_dir or settings.agent_config_dir)
        self._contracts: list[AgentContract] | None = None
        self._runtime_profiles: dict[str, AgentRuntimeProfile] | None = None

    def list_agents(self) -> list[AgentContract]:
        if self._contracts is None:
            agents: list[AgentContract] = []
            for path in sorted(self.config_dir.glob("*.yaml")):
                with path.open("r", encoding="utf-8") as handle:
                    agents.append(AgentContract.model_validate(yaml.safe_load(handle)))
            self._contracts = agents
        return self._contracts

    def get_agents_for_role(self, role: str) -> list[AgentContract]:
        return [agent for agent in self.list_agents() if agent.role == role and agent.status == "active"]

    def get_agent_for_role(self, role: str) -> AgentContract | None:
        agents = self.get_agents_for_role(role)
        return agents[0] if agents else None

    def get_runtime_profile_for_role(self, role: str) -> AgentRuntimeProfile | None:
        if self._runtime_profiles is None:
            self._runtime_profiles = {}
            for agent in self.list_agents():
                if agent.status != "active":
                    continue
                materials: list[ReferenceMaterial] = []
                for material_ref in agent.material_refs:
                    path = Path(material_ref.path)
                    if not path.is_absolute():
                        path = PROJECT_ROOT / path
                    with path.open("r", encoding="utf-8") as handle:
                        materials.append(
                            ReferenceMaterial(
                                name=material_ref.name,
                                purpose=material_ref.purpose,
                                content=handle.read(),
                            )
                        )
                self._runtime_profiles[agent.role] = AgentRuntimeProfile(
                    id=agent.id,
                    role=agent.role,
                    purpose=agent.purpose,
                    expected_outputs=agent.expected_outputs,
                    reference_materials=materials,
                )
        return self._runtime_profiles.get(role)
