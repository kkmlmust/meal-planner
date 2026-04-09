FROM docker.io/astral/uv:python3.12-bookworm-slim

WORKDIR /app

# Copy all files first
COPY . .

# Create venv and install dependencies
RUN uv venv --python python3.12 && \
    uv pip install -e .

EXPOSE 8765

CMD ["/app/.venv/bin/python", "-m", "recipe_agent.agent"]
