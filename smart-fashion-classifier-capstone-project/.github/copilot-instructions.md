# Smart Fashion Classifier - AI Agent Instructions

## Architecture Overview
This is a microservices-based fashion image classification system with two main components:
- **Gateway Service** (`gateway.py`): Flask REST API that accepts image URLs, preprocesses images for Xception model, and communicates with TensorFlow Serving via gRPC
- **Model Service**: TensorFlow Serving container hosting the fine-tuned Xception model for 15 fashion categories (Belts, Shirts, etc.)

Services communicate internally via gRPC using protobuf serialization (`proto.py`). External clients call the gateway's `/predict` endpoint with JSON `{"url": "image_url"}`.

## Key Patterns & Conventions
- **Image Preprocessing**: Always resize to (299, 299), convert to RGB, normalize to [-1, 1] range for Xception compatibility
- **Model Input/Output**: Input tensor named "input_layer_16", output "output_0" with 15 float probabilities
- **gRPC Communication**: Use `prediction_service_pb2_grpc.PredictionServiceStub` with `PredictRequest` containing model_spec and inputs
- **Dependency Management**: Use Pipenv for Python dependencies; install with `pipenv install --system --deploy`
- **Containerization**: Gateway uses gunicorn for production serving; model uses TensorFlow Serving base image

## Development Workflows
- **Local Development**: Run `docker-compose up` to start both services (gateway on :9696, tf-serving on :8500)
- **Testing**: Use `test.py` to POST image URLs to `http://localhost:9696/predict` (note: test script has hardcoded localhost:8080 for different setups)
- **Model Training**: Refer to `notebooks/smart_fashion_classifier_capstone_project.ipynb` for complete pipeline using Xception fine-tuning
- **Kubernetes Deployment**: Apply `kube-config/` YAMLs; gateway service exposes port 80, model service is internal on 8500

## Critical Files
- `gateway.py`: Main API logic, preprocessing, and gRPC client
- `proto.py`: Numpy array to protobuf conversion utilities
- `clothing-model/`: SavedModel format directory for TensorFlow Serving
- `data/fashion_dataset/`: Training/validation/test images organized by category
- `docker-compose.yaml`: Local development setup with service dependencies

## Common Pitfalls
- Ensure protobuf version compatibility (pinned to 3.20.3 in Pipfile)
- Model expects specific input preprocessing; don't use standard ImageNet preprocessing
- gRPC timeouts default to 20 seconds; adjust for large images if needed
- Kubernetes service names must match environment variables (e.g., `tf-serving-model.default.svc.cluster.local:8500`)</content>
<parameter name="filePath">d:\Learning\zoocamp_learning_path\machine-learning-zoomcamp\smart-fashion-classifier-capstone-project\.github\copilot-instructions.md