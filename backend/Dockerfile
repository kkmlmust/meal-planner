FROM docker.io/astral/uv:python3.12-bookworm-slim

WORKDIR /app

# Copy all files first
COPY . .

# Create venv and install dependencies
RUN uv venv --python python3.12 && \
    uv pip install -e .

EXPOSE 8000

CMD ["sh", "-c", "/app/.venv/bin/python /app/seed.py && /app/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000"]
