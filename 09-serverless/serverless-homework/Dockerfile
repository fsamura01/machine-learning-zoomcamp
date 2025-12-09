FROM agrigorev/model-2025-hairstyle:v1 

# Install required libraries
RUN pip install --no-cache-dir \
    pillow \
    onnxruntime \
    numpy

COPY hair_classifier_v1.onnx.data .
COPY hair_classifier_v1.onnx .
# Copy lambda function code
COPY lambda_function.py ./

# Set the CMD to your handler
CMD ["lambda_function.lambda_handler"]

