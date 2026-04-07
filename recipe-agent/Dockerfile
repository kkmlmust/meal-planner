FROM docker.io/astral/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml ./
RUN uv sync --no-dev

COPY . .

EXPOSE 8765

CMD [".venv/bin/python", "-m", "recipe_agent.agent"]
