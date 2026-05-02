from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: str = "development"
    database_url: str = "sqlite+pysqlite:///:memory:"
    provider: str = "mock"
    model: str = "gpt-oss"
    provider_base_url: str | None = None
    provider_api_key: str | None = None
    worker_poll_interval: int = 2
    agent_config_dir: str = "config/agents"
    supervisor_dir: str = "supervisor"

    model_config = SettingsConfigDict(env_prefix="TASKMIND_", case_sensitive=False, env_file=".env")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
