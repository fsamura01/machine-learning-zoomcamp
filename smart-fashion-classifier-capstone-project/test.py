import requests

# url = "http://localhost:9696/predict"

url = "http://localhost:8080/predict"

data = {"url": "https://bit.ly/49Dxq1l"}

result = requests.post(url, json=data).json()
print(result)
