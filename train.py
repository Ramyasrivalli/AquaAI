"""
train.py — Offline ML Model Training & Artifact Serialization Script.

Trains candidate models on water potability dataset using median imputation and StandardScaler.
Serializes best model, scaler, imputer, and metadata into models/.

Run: python train.py
"""

import json
import pickle
import warnings
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from core.helpers import CSV_PATH, FEATURE_COLS, MODELS_DIR

warnings.filterwarnings("ignore")


def train_pipeline() -> None:
    """Train ML models and save serialized artifacts."""
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Dataset file not found at: {CSV_PATH}")

    print(f"[TRAIN] Loading dataset from '{CSV_PATH}'...")
    df = pd.read_csv(CSV_PATH)

    X = df[FEATURE_COLS]
    y = df["Potability"]

    # 1. Imputation & Scaling
    imputer = SimpleImputer(strategy="median")
    X_imputed = imputer.fit_transform(X)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_imputed)

    # 2. Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )

    # 3. Model Comparison
    models = {
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
        "Support Vector Machine": SVC(probability=True, random_state=42),
        "Decision Tree": DecisionTreeClassifier(random_state=42),
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
    }

    results = {}
    trained_models = {}

    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)

        results[name] = {
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
        }
        trained_models[name] = model
        print(f"  - {name:25s} | Acc: {acc:.4f} | Prec: {prec:.4f} | Rec: {rec:.4f} | F1: {f1:.4f}")

    best_name = max(results, key=lambda k: results[k]["accuracy"])
    best_model = trained_models[best_name]

    print(f"\n[TRAIN] Best Performing Model: '{best_name}' (Accuracy: {results[best_name]['accuracy']})")

    # 4. Serialize Artifacts
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODELS_DIR / "best_model.pkl", "wb") as f:
        pickle.dump(best_model, f)

    with open(MODELS_DIR / "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)

    with open(MODELS_DIR / "imputer.pkl", "wb") as f:
        pickle.dump(imputer, f)

    meta_data = {
        "best_model_name": best_name,
        "feature_columns": FEATURE_COLS,
        "metrics": results,
    }
    with open(MODELS_DIR / "model_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta_data, f, indent=2)

    print(f"[TRAIN] Artifacts saved to '{MODELS_DIR}'")


if __name__ == "__main__":
    train_pipeline()
