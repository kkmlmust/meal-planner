from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    backend_url: str = Field(default="http://localhost:8000", alias="RECIPE_AGENT_BACKEND_URL")
    api_key: str = Field(..., alias="RECIPE_API_KEY")

    model_config = {"env_file": ".env.docker.secret", "populate_by_name": True}


settings = Settings()
