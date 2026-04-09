FROM docker.io/astral/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml ./
RUN uv venv && uv pip install \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.30.0" \
    "sqlmodel>=0.0.22" \
    "asyncpg>=0.30.0" \
    "psycopg2-binary>=2.9.0" \
    "sqlalchemy[asyncio]>=2.0.35" \
    "pydantic-settings>=2.6.0" \
    "alembic>=1.14.0"

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "/app/.venv/bin/python /app/seed.py && /app/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000"]
