FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY ["pyproject.toml", "uv.lock", "./"]

RUN uv sync --locked

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY "ping/ping.py" .

EXPOSE 9696

ENTRYPOINT [".venv/bin/gunicorn", "--bind=0.0.0.0:9696", "ping:app"]