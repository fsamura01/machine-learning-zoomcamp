import requests

customer = {
    "customer": {
        "gender": "female",
        "seniorcitizen": 0,
        "partner": "yes",
        "dependents": "no",
        "phoneservice": "no",
        "multiplelines": "no_phone_service",
        "internetservice": "dsl",
        "onlinesecurity": "no",
        "onlinebackup": "yes",
        "deviceprotection": "no",
        "techsupport": "no",
        "streamingtv": "no",
        "streamingmovies": "no",
        "contract": "month-to-month",
        "paperlessbilling": "yes",
        "paymentmethod": "electronic_check",
        "tenure": 1,
        "monthlycharges": 29.85,
        "totalcharges": 29.85,
    }
}

url = "http://localhost:8080/2015-03-31/functions/function/invocations"

result = requests.post(url, json=customer).json()
print(result)
