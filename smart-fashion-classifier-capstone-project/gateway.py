#!/usr/bin/env python
# coding: utf-8

import os
from io import BytesIO

import grpc
import numpy as np
import requests
from flask import Flask, jsonify, request
from PIL import Image
from tensorflow_serving.apis import predict_pb2, prediction_service_pb2_grpc

from proto import np_to_protobuf

print("Imports successful!")

app = Flask("smart-fashion-classifier")

host = os.getenv("TF_SERVING_HOST", "localhost:8500")
channel = grpc.insecure_channel(host)
prediction_service_stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)


def preprocess_image(url):
    """Custom preprocessing for Xception model"""
    # Download image
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))

    # Convert to RGB if needed
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Resize to Xception input size
    img = img.resize((299, 299), Image.LANCZOS)

    # Convert to numpy array and normalize
    x = np.array(img, dtype=np.float32)

    # Xception preprocessing: scale to [-1, 1]
    x = x / 127.5 - 1.0

    # Add batch dimension
    X = np.expand_dims(x, axis=0)

    return X


def prepare_request(X):
    predict_request = predict_pb2.PredictRequest()
    predict_request.model_spec.name = "clothing-model"
    predict_request.model_spec.signature_name = "serving_default"
    predict_request.inputs["input_layer_16"].CopyFrom(np_to_protobuf(X))
    print("Success! Data loaded into request.")
    return predict_request


category_names = [
    "Belts",
    "Briefs",
    "Casual Shoes",
    "Flip Flops",
    "Handbags",
    "Heels",
    "Kurtas",
    "Sandals",
    "Shirts",
    "Sports Shoes",
    "Sunglasses",
    "Tops",
    "Tshirts",
    "Wallets",
    "Watches",
]


def prepare_response(predict_response):
    pred = predict_response.outputs["output_0"].float_val
    return dict(zip(category_names, pred))


def predict(url):
    X = preprocess_image(url)
    predict_request = prepare_request(X)
    predict_response = prediction_service_stub.Predict(predict_request, timeout=20.0)
    response = prepare_response(predict_response)
    return response


@app.route("/predict", methods=["POST"])
def predict_endpoint():
    data = request.get_json()
    url = data["url"]
    response = predict(url)
    return jsonify(response)


if __name__ == "__main__":
    url = "https://bit.ly/49Dxq1l"
    predict_response = predict(url)
    print(predict_response)
    # app.run(debug=True, host="0.0.0.0", port=9696)
