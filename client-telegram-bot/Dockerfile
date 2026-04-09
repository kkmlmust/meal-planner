FROM docker.io/astral/uv:python3.12-bookworm-slim

WORKDIR /app

# Copy all files first
COPY . .

# Create venv and install dependencies
RUN uv venv --python python3.12 && \
    uv pip install -e .

CMD ["/app/.venv/bin/python", "-m", "telegram_bot.bot"]
