FROM docker.io/astral/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml ./
RUN uv venv && uv pip install \
    "python-telegram-bot>=21.0" \
    "websockets>=13.0" \
    "pydantic-settings>=2.6.0"

COPY . .

CMD ["/app/.venv/bin/python", "-m", "telegram_bot.bot"]
