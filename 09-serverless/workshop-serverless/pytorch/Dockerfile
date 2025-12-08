FROM public.ecr.aws/lambda/python:3.13

RUN pip install onnxruntime keras-image-helper

COPY clothing_classifier_mobilenet_v2_latest.onnx .
COPY lambda_function.py ./

CMD ["lambda_function.lambda_handler"]