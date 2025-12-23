import requests

url = "http://localhost:9696/predict"

sample = {
    "ph": 5.584086638456089,
    "hardness": 188.3133237696164,
    "solids": 28748.68773904612,
    "chloramines": 7.54486878877965,
    "sulfate": 393.66339551509645,
    "conductivity": 280.4679159334877,
    "organic_carbon": 8.399734640152758,
    "trihalomethanes": 54.917861841994466,
    "turbidity": 2.5597082275565217,
}

# sample = {
#     "ph": 9.445129837868656,
#     "hardness": 145.80540244684383,
#     "solids": 13168.529155675998,
#     "chloramines": 9.44447108562294,
#     "sulfate": 310.583373858597,
#     "conductivity": 592.6590209759507,
#     "organic_carbon": 8.606396746986945,
#     "trihalomethanes": 77.57745951035697,
#     "turbidity": 3.8751652466165467,
# }

# Just send the JSON directly - FastAPI handles everything!
response = requests.post(url, json=sample)

if response.status_code == 200:
    result = response.json()
    print(f"Potable: {result['potable']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Recommendation: {result['recommendation']}")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
