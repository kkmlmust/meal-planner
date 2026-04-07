FROM docker.io/astral/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml ./
RUN uv sync --no-dev

COPY . .

CMD [".venv/bin/python", "-m", "telegram_bot.bot"]
