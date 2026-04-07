from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    bot_token: str = Field(..., alias="BOT_TOKEN")
    agent_ws_url: str = Field(default="ws://localhost:8765/ws/chat", alias="NANOBOT_WS_URL")
    agent_access_key: str = Field(default="local-agent-key", alias="NANOBOT_ACCESS_KEY")

    model_config = {"env_file": ".env.docker.secret", "populate_by_name": True}


settings = Settings()
