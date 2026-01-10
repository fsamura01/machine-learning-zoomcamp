import requests

url = "http://localhost:8080/predict"

#url = "http://localhost:9696/predict"

data = {"url": "https://raw.githubusercontent.com/fsamura01/machine-learning-zoomcamp/main/smart-fashion-classifier-capstone-project/10005.jpg"}

result = requests.post(url, json=data).json()
print(result)
