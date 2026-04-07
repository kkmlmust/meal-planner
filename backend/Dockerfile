FROM docker.io/astral/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml ./
RUN uv sync --no-dev

COPY . .

EXPOSE 8000

CMD ["sh", "-c", ".venv/bin/python seed.py && .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000"]
