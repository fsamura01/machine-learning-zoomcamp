# Docker and Kubernetes ML Model Deployment Documentation

This repository contains a machine learning model deployment setup using TensorFlow Serving and a Flask gateway, containerized with Docker and deployable to Kubernetes. The project demonstrates serving a clothing classification model (Xception-based) via HTTP API, with gRPC communication to TF Serving.

## Project Overview

- **Gateway Service** (`gateway.py`): A Flask app that exposes a `/predict` POST endpoint on port 9696. It preprocesses images from URLs using Keras Image Helper and forwards predictions to TensorFlow Serving via gRPC.
- **Model Service** (`clothing-model/`): TensorFlow SavedModel served by TF Serving on port 8500.
- **Containerization**: Docker Compose for local development, with Kubernetes manifests for production.
- **Key Dependencies**: Flask, TensorFlow Serving API, Keras Image Helper, gRPC.

## Architecture

```
Client (HTTP POST) → Gateway (Flask + Preprocessing) → TF Serving (gRPC) → Predictions (JSON)
```

- Gateway handles HTTP requests, image preprocessing (resize to 299x299), and response formatting.
- TF Serving loads the SavedModel and performs inference.
- Environment variable `TF_SERVING_HOST` configures the gRPC endpoint (defaults to `localhost:8500`).

## Quick Start

### Prerequisites
- Docker Desktop installed and running.
- Python 3.11+ (for local testing).
- Git (to clone the repo).

### Local Setup with Docker Compose

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/fsamura01/machine-learning-zoomcamp.git
   cd machine-learning-zoomcamp/10-kubernetes
   ```

2. **Build and Run Services**:
   ```bash
   docker-compose up --build
   ```
   - This starts two containers: `clothing-model` (TF Serving) and `gateway` (Flask).
   - Gateway listens on `http://localhost:9696`, TF Serving on internal port 8500.

3. **Test the API**:
   ```bash
   python test.py
   ```
   - Sends a sample image URL to `/predict` and prints class probabilities (e.g., `{"pants": 0.95, ...}`).

4. **Stop Services**:
   ```bash
   docker-compose down
   ```

### Local Development (Without Docker)

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt  # Based on pyproject.toml
   ```

2. **Start TF Serving**:
   ```bash
   docker run -p 8500:8500 -v $(pwd)/clothing-model:/models/clothing-model -e MODEL_NAME=clothing-model tensorflow/serving:latest
   ```

3. **Run Gateway**:
   ```bash
   python gateway.py
   ```
   - Access at `http://localhost:9696/predict`.

## Docker Monitoring and Troubleshooting

### Viewing Container Processes

To inspect running processes inside containers (e.g., via Docker Desktop or CLI):

1. **Open Docker Desktop**:
   - Go to **Containers** tab.
   - Select `10-kubernetes-gateway-1` or `10-kubernetes-clothing-model-1`.
   - Click **Exec** to open a shell, then run `ps aux`.

2. **Sample Output from Gateway Container**:
   ```
   USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
   root         1  0.0  0.4  93952 32088 ?        Ssl  16:31   0:00 uv run gunicorn --bind=0.0.0.0:9696 gate
   root        10  0.0  0.4  38736 29096 ?        S    16:31   0:01 /app/.venv/bin/python /app/.venv/bin/gun
   root        11  0.5  9.0 3102260 635504 ?      Sl   16:31   0:25 /app/.venv/bin/python /app/.venv/bin/gun
   root        42  0.0  0.0   2680  1536 pts/0    Ss   17:01   0:00 /bin/sh
   root       102  0.0  0.0      0     0 pts/0    Z    17:54   0:00 [dpkg-preconfigu] <defunct>
   root       170  0.0  0.0   6792  3712 pts/0    R+   17:55   0:00 ps aux
   ```

   - **PID 1**: Main Gunicorn process (WSGI server for Flask).
   - **PID 10-11**: Gunicorn workers handling requests (higher memory for preprocessing/inference).
   - **PID 42**: Interactive shell (from `docker exec`).
   - **PID 102**: Zombie process (harmless leftover from container build).
   - **PID 170**: The `ps aux` command itself.

   For TF Serving container, expect ~59 processes (threads for model serving).

### Monitoring Resource Usage

Use `docker stats` or Docker Desktop's **Stats** tab for real-time metrics:

```
CONTAINER ID   NAME                             CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O       PIDS
741c0e734f88   10-kubernetes-clothing-model-1   0.11%     398.4MiB / 6.731GiB   5.78%     4.3MB / 7.31kB    93.1MB / 0B     59
ff4f072553e6   10-kubernetes-gateway-1          0.20%     326MiB / 6.731GiB     4.73%     12.9MB / 4.63MB   648MB / 121MB   32
```

- **Clothing-Model**: Low CPU (idle), ~400MB memory (model loading), high disk read (loading SavedModel).
- **Gateway**: Slightly higher CPU (request handling), ~326MB memory (Flask + preprocessing), network I/O from HTTP/gRPC traffic.

### Common Issues and Fixes

1. **gRPC Connection Failed**:
   - Error: "✗ Failed: {e}" in gateway logs.
   - Cause: TF Serving not reachable (check `TF_SERVING_HOST`).
   - Fix: Ensure `docker-compose up` started both services. Verify with `docker ps`.

2. **Port Conflicts**:
   - If 9696/8500 are in use, stop conflicting services or change ports in `docker-compose.yaml`.

3. **High Resource Usage**:
   - Monitor with `docker stats`. Restart if memory >90%: `docker-compose restart`.

4. **Model Not Loading**:
   - Check TF Serving logs: `docker logs 10-kubernetes-clothing-model-1`.
   - Ensure `clothing-model/` directory is mounted correctly.

5. **Prediction Errors**:
   - Verify input: POST JSON `{"url": "http://bit.ly/mlbookcamp-pants"}` to `http://localhost:9696/predict`.
   - Check gateway logs for preprocessing or gRPC issues.

## Kubernetes Deployment

For production, deploy to Kubernetes using manifests in `kube-config/`:

1. **Apply Manifests**:
   ```bash
   kubectl apply -f kube-config/
   ```

2. **Check Status**:
   ```bash
   kubectl get pods,svc
   ```

3. **Port Forward for Testing**:
   ```bash
   kubectl port-forward svc/gateway 9696:80
   ```
   - Access at `http://localhost:9696/predict`.

- Services: `tf-serving-clothing-model` (gRPC) and `gateway` (HTTP LoadBalancer).
- Resources: CPU/memory limits set (e.g., gateway: 200m CPU, 256Mi memory).

## API Usage

- **Endpoint**: `POST /predict`
- **Input**: `{"url": "<image_url>"}`
- **Output**: `{"dress": 0.01, "hat": 0.02, ..., "t-shirt": 0.95}`
- **Classes**: dress, hat, longsleeve, outwear, pants, shirt, shoes, shorts, skirt, t-shirt.

Example with curl:
```bash
curl -X POST http://localhost:9696/predict -H "Content-Type: application/json" -d '{"url": "http://bit.ly/mlbookcamp-pants"}'
```

## File Structure

- `gateway.py`: Flask app with preprocessing and gRPC client.
- `proto.py`: Helper for NumPy to TensorProto conversion.
- `test.py`: Client script for testing.
- `docker-compose.yaml`: Local container orchestration.
- `image-gateway.dockerfile` / `image-model.dockerfile`: Docker builds.
- `kube-config/`: Kubernetes YAMLs.
- `clothing-model/`: SavedModel artifacts.
- `pyproject.toml`: Python dependencies.

## Contributing

- Test locally with `python test.py`.
- Ensure `pyproject.toml` includes new deps.
- Update docs for changes.

For issues, check logs with `docker-compose logs` or `kubectl logs`. Refer to model description in `model-description.txt` for I/O details.