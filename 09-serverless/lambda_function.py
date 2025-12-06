#!/bin/bash
#!/usr/bin/env python
# coding: utf-8
import tflite_runtime.interpreter as tflite
from keras_image_helper import create_preprocessor

interpreter = tflite.Interpreter(model_path="clothing-model.tflite")
interpreter.allocate_tensors()

input_index = interpreter.get_input_details()[0]["index"]
output_index = interpreter.get_output_details()[0]["index"]

preprocessor = create_preprocessor("xception", target_size=(299, 299))

# url = "http://bit.ly/mlbookcamp-pants"

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


def predict(url):
    X = preprocessor.from_url(url)

    interpreter.set_tensor(input_index, X)
    interpreter.invoke()
    preds = interpreter.get_tensor(output_index)

    # What happens here is we take an numpy array and it will converted to usual
    # python list with usul python floats.
    float_predictions = preds[0].tolist()

    return dict(zip(classes, float_predictions))


def lambda_handler(event, context):
    url = event["url"]
    result = predict(url)
    return result
