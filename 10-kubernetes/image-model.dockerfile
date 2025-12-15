FROM tensorflow/serving:2.7.0

# Copy model in the image
COPY clothing-model /models/clothing-model/1
# Specify environmental variable
ENV MODEL_NAME="clothing-model"