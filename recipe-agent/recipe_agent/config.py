from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # LLM connection (via qwen-code-api OAuth proxy)
    llm_base_url: str = Field(default="http://localhost:8080/v1", alias="RECIPE_AGENT_LLM_BASE_URL")
    llm_api_key: str = Field(default="sk-qwen-local", alias="RECIPE_AGENT_LLM_API_KEY")
    llm_model: str = Field(default="coder-model", alias="RECIPE_AGENT_LLM_MODEL")

    # Agent access
    access_key: str = Field(default="local-agent-key", alias="RECIPE_AGENT_ACCESS_KEY")

    # Backend (for MCP tools to call)
    backend_url: str = Field(default="http://localhost:8000", alias="RECIPE_AGENT_BACKEND_URL")
    backend_api_key: str = Field(default="", alias="RECIPE_API_KEY")

    # Telegram default user (for --test mode)
    default_telegram_id: str = Field(default="test_user_1", alias="DEFAULT_TELEGRAM_ID")

    # Server
    host: str = Field(default="0.0.0.0", alias="AGENT_HOST")
    port: int = Field(default=8765, alias="AGENT_PORT")

    model_config = {"env_file": ".env.docker.secret", "populate_by_name": True}


settings = Settings()
