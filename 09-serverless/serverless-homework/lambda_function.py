from io import BytesIO
from urllib import request

import numpy as np
import onnxruntime as ort
from PIL import Image

# Load the model
model_path = "hair_classifier_v1.onnx"


def download_image(url):
    with request.urlopen(url) as resp:
        buffer = resp.read()
    stream = BytesIO(buffer)
    img = Image.open(stream)
    return img


def prepare_image(img, target_size):
    if img.mode != "RGB":
        img = img.convert("RGB")
    img = img.resize(target_size, Image.NEAREST)
    return img


def preprocess_input(img):
    # Convert to numpy array
    x = np.array(img, dtype=np.float32)

    # Normalize to [0, 1]
    x = x / 255.0

    # ImageNet standardization
    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])

    # Normalize
    x = (x - mean) / std

    # Transpose to channel-first format (C, H, W) and add batch dimension
    x = x.transpose(2, 0, 1)

    x = np.expand_dims(x, axis=0)

    return x.astype(np.float32)


session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name
input_shape = session.get_inputs()[0].shape
input_type = session.get_inputs()[0].type

print(f"Input name: {input_name}")
print(f"Output name: {output_name}")
print(f"Input shape: {input_shape}")
print(f"Input type: {input_type}")


def predict(url):
    # Download and prepare image
    img = download_image(url)
    img = prepare_image(img, target_size=(200, 200))

    # Preprocess
    X = preprocess_input(img)
    print(f"Provided shape: {X.shape}")
    print(f"Provided dtype: {X.dtype}")

    # Run inference - FIX: pass None or [output_name] instead of output_name
    outputs = session.run([output_name], {input_name: X})
    print(f"outputs: {outputs}")
    float_predictions = float(outputs[0][0])

    return float_predictions


def lambda_handler(event, context):
    url = event["url"]
    result = predict(url)

    return {"statusCode": 200, "body": result}
