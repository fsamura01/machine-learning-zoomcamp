FROM tensorflow/serving:latest

COPY clothing-model /models/clothing-model
ENV MODEL_NAME="clothing-model"