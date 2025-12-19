#!/usr/bin/env python
# coding: utf-8
import os

import grpc

# import tensorflow as tf
from flask import Flask, jsonify, request
from keras_image_helper import create_preprocessor

# from tensorflow import make_tensor_proto
from tensorflow_serving.apis import predict_pb2, prediction_service_pb2_grpc

from proto import np_to_protobuf

preprocessor = create_preprocessor("xception", target_size=(299, 299))


host = os.getenv(
    "TF_SERVING_HOST", "localhost:8500"
)  # default: localhost:8500:tf-serving:8500
channel = grpc.insecure_channel(host)
prediction_service_stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)

try:
    grpc.channel_ready_future(channel).result(timeout=5)
    print("✓ Connected using container name!")
except Exception as e:
    print(f"✗ Failed: {e}")

app = Flask("Gateway")


def prepare_request(X):
    predict_request = predict_pb2.PredictRequest()

    predict_request.model_spec.name = "clothing-model"
    predict_request.model_spec.signature_name = "serving_default"

    predict_request.inputs["input_8"].CopyFrom(np_to_protobuf(X))

    return predict_request


classes = [
    "dress",
    "hat",
    "longsleeve",
    "outwear",
    "pants",
    "shirt",
    "shoes",
    "shorts",
    "skirt",
    "t-shirt",
]


def prepare_response(predict_response):
    predictions = predict_response.outputs["dense_7"].float_val
    print(predictions)

    return dict(zip(classes, predictions))


def predict(url):
    X = preprocessor.from_url(url)

    predict_request = prepare_request(X)
    predict_response = prediction_service_stub.Predict(predict_request, timeout=20.0)
    response = prepare_response(predict_response)
    return response


@app.route("/predict", methods=["POST"])
def predict_endpoint():
    data = request.get_json()
    url = data["url"]
    result = predict(url)

    return jsonify(result)


if __name__ == "__main__":
    # url = "http://bit.ly/mlbookcamp-pants"
    # response = predict(url)
    # print(response)
    app.run(debug=True, host="0.0.0.0", port=9696)
