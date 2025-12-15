FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY ["pyproject.toml", "uv.lock", "./"]

RUN uv sync --locked

COPY ["gateway.py", "proto.py", "./"]

EXPOSE 9696

ENTRYPOINT ["uv", "run", "gunicorn", "--bind=0.0.0.0:9696", "gateway:app"]