## Purpose

Short, actionable guidance for AI coding agents working on this repo.

## Big picture

- **Service**: A small Flask gateway (`gateway.py`) exposes a `/predict` POST endpoint on port `9696` and forwards requests to TensorFlow Serving over gRPC.
- **Model artifacts**: Two model forms live in the repo: `clothing-model.h5` and a SavedModel directory `clothing-model/` (contains `saved_model.pb` and `variables/`). TensorFlow Serving is the runtime expected for inference.
- **Why**: The gateway decouples HTTP clients from TF Serving (gRPC) and handles image preprocessing using `keras_image_helper`.

## Key files to inspect

- [main.py](main.py) — tiny entrypoint/demo, not the service.
- [gateway.py](gateway.py) — main service: Flask app, preprocessing, gRPC Predict request construction and response mapping.
- [model-description.txt](model-description.txt) — documents model signature: input `input_8`, output `dense_7`, signature `serving_default`.
- [pyproject.toml](pyproject.toml) — lists runtime deps and Python >= 3.11.
- [test.py](test.py) — example client that posts JSON to the gateway.

## Integration & runtime notes (concrete)

- Gateway uses gRPC to a TF Serving address taken from the environment variable `TF_SERVING_HOST` (defaults to `localhost:8500`). Set this when your TF Serving container runs on a different host or Docker network.
- The gateway uses a small local helper `proto.np_to_protobuf(data)` (see `proto.py`) to convert NumPy arrays into TensorProto objects. This replaces the previous use of `tensorflow.make_tensor_proto`.
- The startup includes a gRPC readiness check (`grpc.channel_ready_future(channel).result(timeout=5)`) — expect a short timeout error if TF Serving is not reachable.
- Predict request details:
  - `model_spec.name = "clothing-model"`
  - `model_spec.signature_name = "serving_default"`
  - input tensor key: `input_8` (gateway copies `np_to_protobuf(X)` into `inputs["input_8"]`).
  - output tensor key: `dense_7` (gateway reads `predict_response.outputs["dense_7"].float_val`).
- Preprocessing: created with `create_preprocessor("xception", target_size=(299, 299))` — keep input size and model-specific preprocessor in sync with the SavedModel.


## How to run locally (examples)

- Start TensorFlow Serving (example, adapt host paths on Windows):

  docker run --rm -p 8500:8500 -p 8501:8501 -v $(pwd)/clothing-model:/models/clothing-model -e MODEL_NAME=clothing-model tensorflow/serving:latest

- Run the gateway (note: current `gateway.py` default `__main__` executes a single sample prediction and does not start the Flask server — see notes):

  # set TF Serving host (PowerShell)
  $env:TF_SERVING_HOST = "localhost:8500"
  python gateway.py

- To run the Flask server for continuous HTTP serving, open `gateway.py` and either uncomment the `app.run(...)` line in `if __name__ == "__main__"` or modify the block to call `app.run(...)`. After that use:

  python gateway.py

- Test with the included example client (when Flask server is running):

  python test.py

  Or POST JSON to `http://localhost:9696/predict`:

  {"url": "http://bit.ly/mlbookcamp-pants"}

## Docker images & docker-compose

- The repo includes two Dockerfiles and a `docker-compose.yaml` to run the model and the gateway as services:
  - `image-model.dockerfile` — builds a TF Serving image and copies the `clothing-model` SavedModel into `/models/clothing-model/1`. It sets `MODEL_NAME="clothing-model"` in the image.
  - `image-gateway.dockerfile` — builds the Flask gateway image; the image starts `gateway:app` with Gunicorn via `uv`.
  - `docker-compose.yaml` — composes two services: `clothing-model` (TF Serving image `clothing-model:xception-v4-001`) and `gateway` (`clothing-model-gateway:001`). The compose file already sets `TF_SERVING_HOST=clothing-model:8500` for the gateway and maps port `9696:9696`.

- Build the images locally (run from repo root):

  docker build -f image-model.dockerfile -t clothing-model:xception-v4-001 .
  docker build -f image-gateway.dockerfile -t clothing-model-gateway:001 .

- Start both services with docker-compose (rebuild images if needed):

  docker-compose up --build

- Notes:
  - `TF_SERVING_HOST` in the compose file is set to `clothing-model:8500`, so the gateway will connect to TF Serving using the service name reachable on the Docker network.
  - The TF Serving image exposes GRPC on `8500` (container) — ensure your host does not need direct access unless you plan to map the port in `docker-compose.yaml`.
  - The model image uses `tensorflow/serving:2.7.0` and copies the model into the `1` version subfolder — TF Serving will expose it as `clothing-model`.


## Dependencies & environment

- Use Python >= 3.11 (see `pyproject.toml`). Key packages: `flask`, `tensorflow`, `keras-image-helper`, `tensorflow-serving-api` (gRPC stubs used in `gateway.py`).
- The repo relies on TensorFlow Serving (gRPC) rather than in-process TF when `gateway.py` is used.

## Patterns & conventions specific to this repo

- Keep model I/O names unchanged: `input_8` and `dense_7` are referenced directly in code and `model-description.txt`.
- The gateway constructs gRPC PredictRequests (not REST) — agents should avoid changing the RPC style unless also updating the client/test tooling.
- Preprocessing is centralized in `gateway.py` via `preprocessor = create_preprocessor(...)`; follow the same helper for new endpoints.

## What to change when updating the model

- If you replace the model, update `model_spec.name`, signature name, or tensor keys in `gateway.py` and `model-description.txt` to prevent runtime mismatch.
- When testing locally, rebuild the SavedModel under `clothing-model/` and restart TF Serving container.

## Quick checks an AI agent should run before applying changes

- Confirm `pyproject.toml` deps cover any new imports.
- Run `python gateway.py` and `python test.py` (or curl) to validate end-to-end after changes.

## Where to ask for clarification

- If model input/output keys are unclear, inspect `clothing-model/saved_model.pb` with `saved_model_cli` or consult `model-description.txt` present in the repo.

---
If anything above is unclear or you'd like a different level of detail (for example, automated Docker compose snippets or test harnesses), tell me which parts to expand.

## Troubleshooting & common issues

- gRPC connection failures: when `grpc.channel_ready_future(channel).result(timeout=5)` times out, verify `TF_SERVING_HOST` is set and reachable from the gateway container/host. Example (PowerShell):

  $env:TF_SERVING_HOST = "localhost:8500"

- Model not found / wrong signature: ensure the SavedModel is placed under `clothing-model/1` (or the path expected by your TF Serving image) and that `model_spec.name` and `signature_name` match `model-description.txt`.
- TensorProto conversion issues: the gateway uses `proto.np_to_protobuf()` which expects `float32` NumPy arrays. If you change preprocessing, confirm the dtype and shape match the model input.
- Long prediction latency / timeout: `prediction_service_stub.Predict(..., timeout=20.0)` uses a 20s timeout — increase if your model warmup or network is slow.

## docker-compose: map TF Serving ports for direct access

- By default `docker-compose.yaml` connects `gateway` to the `clothing-model` service on the internal Docker network. If you need host access to TF Serving (gRPC 8500 or REST 8501), add port mappings to the `clothing-model` service:

```yaml
services:
  clothing-model:
    image: clothing-model:xception-v4-001
    ports:
      - "8500:8500" # gRPC
      - "8501:8501" # REST
```

- After mapping, you can point `TF_SERVING_HOST` at `localhost:8500` from the host machine for local testing.

