FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files
COPY ["pyproject.toml", "./"]

# Install Python dependencies
RUN pip install --no-cache-dir \
    flask \
    grpcio \
    protobuf==3.20.3 \
    tensorflow-serving-api \
    numpy \
    pillow \
    requests \
    gunicorn

# Copy application files
COPY ["gateway.py", "proto.py", "./"]

# Expose port
EXPOSE 9696

# Run with gunicorn
ENTRYPOINT ["gunicorn", "--bind=0.0.0.0:9696", "gateway:app"]