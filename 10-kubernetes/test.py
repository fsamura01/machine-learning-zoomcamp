import requests

# url = "http://localhost:9696/predict"

# data = {"url": "http://bit.ly/mlbookcamp-pants"}

# result = requests.post(url, json=data).json()
# print(result)


# url = "http://localhost:9696/predict"
url = "http://localhost:9696/predict"
data = {"url": "http://bit.ly/mlbookcamp-pants"}

response = requests.post(url, json=data)
print(response)
print(f"Status Code: {response.status_code}")
print(f"Response Headers: {response.headers}")
print(f"Response Text: {response.text}")

if response.status_code == 200:
    try:
        result = response.json()
        print(f"JSON Result: {result}")
    except:
        print("Response is not valid JSON")
else:
    print(f"Error: Server returned status code {response.status_code}")
