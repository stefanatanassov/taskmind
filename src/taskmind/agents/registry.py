from __future__ import annotations

from pathlib import Path

import yaml

from taskmind.config import get_settings


class AgentRegistry:
    def __init__(self, config_dir: str | None = None) -> None:
        settings = get_settings()
        self.config_dir = Path(config_dir or settings.agent_config_dir)

    def list_agents(self) -> list[dict]:
        agents: list[dict] = []
        for path in sorted(self.config_dir.glob("*.yaml")):
            with path.open("r", encoding="utf-8") as handle:
                agents.append(yaml.safe_load(handle))
        return agents

    def get_agents_for_role(self, role: str) -> list[dict]:
        return [agent for agent in self.list_agents() if agent.get("role") == role and agent.get("status") == "active"]

