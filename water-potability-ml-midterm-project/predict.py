import pickle

import pandas as pd
from fastapi import FastAPI, HTTPException

from schemas import PredictionResponse, WaterSample

# Load model artifacts
model_file = "model_C=1.0.bin"

with open(model_file, "rb") as f_in:
    artifacts = pickle.load(f_in)
    model = artifacts["model"]
    imputer = artifacts["imputer"]
    feature_names = artifacts["feature_names"]

app = FastAPI(title="Water Potability Prediction API")


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "features": feature_names,
    }


@app.post("/predict", response_model=PredictionResponse)
def predict_potability(sample: WaterSample):
    try:
        # Convert to DataFrame with correct column order
        sample_dict = sample.model_dump()
        df = pd.DataFrame([sample_dict])
        df = df[feature_names]  # Ensure correct order

        # Apply imputation (handles any missing values)
        df_imputed = pd.DataFrame(imputer.transform(df), columns=feature_names)

        # Predict
        prediction = model.predict(df_imputed)[0]
        probability = model.predict_proba(df_imputed)[0]

        # Generate recommendation
        if prediction == 1:
            recommendation = (
                "Water appears safe for consumption based on chemical analysis."
            )
        else:
            recommendation = (
                "Water quality concerns detected. Further testing recommended."
            )

        return {
            "potable": bool(prediction),
            "confidence": float(probability[1]),
            "recommendation": recommendation,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.get("/")
def root():
    return {
        "message": "Water Potability Prediction API",
        "version": "1.0",
        "model": "XGBoost",
        "features": feature_names,
        "endpoints": {
            "/predict": "POST - Predict water potability",
            "/health": "GET - Health check",
            "/docs": "GET - API documentation",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9696)
