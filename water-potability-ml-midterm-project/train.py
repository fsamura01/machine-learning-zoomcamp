import pickle

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

C = 1.0

# Load data
df = pd.read_csv("data/water_potability.csv")
df.columns = df.columns.str.lower()

# Imputation
imputer = SimpleImputer(strategy="median")
X_imputed = imputer.fit_transform(df.drop("potability", axis=1))
feature_names = list(df.drop("potability", axis=1).columns)

X = pd.DataFrame(X_imputed, columns=feature_names)
y = df["potability"]

# Data splitting
X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.4, random_state=42, stratify=y
)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
)

# Training the model
models = {
    "Logistic Regression": LogisticRegression(class_weight="balanced", max_iter=5000),
    "Random Forest": RandomForestClassifier(class_weight="balanced", random_state=42),
}

results = {}

for name, model in models.items():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_val)
    y_proba = model.predict_proba(X_val)[:, 1]

    results[name] = {
        "accuracy": accuracy_score(y_val, y_pred),
        "precision": precision_score(y_val, y_pred),
        "recall": recall_score(y_val, y_pred),
        "f1": f1_score(y_val, y_pred),
        "auc_roc": roc_auc_score(y_val, y_proba),
    }


# Apply SMOTE
smote = SMOTE(random_state=42, k_neighbors=5)
X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)

models = {
    "Logistic Regression": LogisticRegression(class_weight="balanced", max_iter=5000),
    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        class_weight="balanced",
        random_state=42,
    ),
}

# Train the model again
results = {}
for name, model in models.items():
    model.fit(X_train_balanced, y_train_balanced)
    y_pred = model.predict(X_val)
    y_proba = model.predict_proba(X_val)[:, 1]

    results[name] = {
        "accuracy": accuracy_score(y_val, y_pred),
        "precision": precision_score(y_val, y_pred),
        "recall": recall_score(y_val, y_pred),
        "f1": f1_score(y_val, y_pred),
        "auc_roc": roc_auc_score(y_val, y_proba),
    }


# Train XGBoost
xgb_model = XGBClassifier(
    n_estimators=300,  # Number of boosting rounds
    max_depth=6,  # Maximum tree depth
    learning_rate=0.1,  # Step size shrinkage (eta)
    subsample=0.8,  # Fraction of samples used per tree
    colsample_bytree=0.8,  # Fraction of features used per tree
    scale_pos_weight=1.56,  # Handle class imbalance
    gamma=0,  # Minimum loss reduction for split
    min_child_weight=1,  # Minimum sum of instance weight in child
    reg_alpha=0,  # L1 regularization
    reg_lambda=1,  # L2 regularization
    random_state=42,
    n_jobs=-1,
    eval_metric="logloss",  # Evaluation metric
)

xgb_model.fit(
    X_train_balanced,
    y_train_balanced,
)

print("Training XGBoost model...")
xgb_model.fit(X_train_balanced, y_train_balanced)

# Evaluate
y_pred = xgb_model.predict(X_test)
print("\n" + "=" * 60)
print("TEST SET PERFORMANCE:")
print("=" * 60)
print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
print(f"F1-Score: {f1_score(y_test, y_pred):.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=["Non-Potable", "Potable"]))

# Save model with ALL artifacts
model_artifacts = {
    "model": xgb_model,
    "imputer": imputer,
    "feature_names": feature_names,
}

output_file = "model_C=1.0.bin"
with open(output_file, "wb") as f_out:
    pickle.dump(model_artifacts, f_out)

print(f"\n✅ Model saved to {output_file}")
print(f"Model includes: XGBoost model, imputer, and feature names")
