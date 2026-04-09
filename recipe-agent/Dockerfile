FROM docker.io/astral/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml ./
# Install only dependencies (skip building the project itself)
RUN uv venv && uv pip install websockets "mcp>=1.0.0" "openai>=1.50.0" "pydantic-settings>=2.6.0"

COPY . .

EXPOSE 8765

CMD ["/app/.venv/bin/python", "-m", "recipe_agent.agent"]
