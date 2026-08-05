"""
helpers.py — Project Configuration & Data Constants.
"""

from typing import Any, Dict, List
from config.settings import (
    ASSETS_DIR,
    BASE_DIR,
    CSV_PATH,
    DB_PATH,
    IMPUTER_PATH,
    META_PATH,
    MODEL_PATH,
    MODELS_DIR,
    SCALER_PATH,
    STATIC_DIR,
    TEMPLATES_DIR,
)

FEATURE_COLS: List[str] = [
    "ph",
    "Hardness",
    "Solids",
    "Chloramines",
    "Sulfate",
    "Conductivity",
    "Organic_carbon",
    "Trihalomethanes",
    "Turbidity",
]

FEATURE_LABELS: Dict[str, str] = {
    "ph": "pH",
    "Hardness": "Hardness",
    "Solids": "Total Dissolved Solids (TDS)",
    "Chloramines": "Chloramines",
    "Sulfate": "Sulfate",
    "Conductivity": "Conductivity",
    "Organic_carbon": "Organic Carbon (TOC)",
    "Trihalomethanes": "Trihalomethanes (THM)",
    "Turbidity": "Turbidity",
}

FEATURE_UNITS: Dict[str, str] = {
    "ph": "",
    "Hardness": "mg/L",
    "Solids": "ppm",
    "Chloramines": "ppm",
    "Sulfate": "mg/L",
    "Conductivity": "μS/cm",
    "Organic_carbon": "ppm",
    "Trihalomethanes": "μg/L",
    "Turbidity": "NTU",
}

VALIDATION_RANGES: Dict[str, Dict[str, float]] = {
    "ph": {"min": 0.0, "max": 14.0, "default": 7.20, "step": 0.1},
    "Hardness": {"min": 0.0, "max": 1000.0, "default": 196.3, "step": 1.0},
    "Solids": {"min": 0.0, "max": 100000.0, "default": 14200.0, "step": 100.0},
    "Chloramines": {"min": 0.0, "max": 20.0, "default": 7.13, "step": 0.1},
    "Sulfate": {"min": 0.0, "max": 1000.0, "default": 333.0, "step": 1.0},
    "Conductivity": {"min": 0.0, "max": 3000.0, "default": 421.0, "step": 5.0},
    "Organic_carbon": {"min": 0.0, "max": 50.0, "default": 14.1, "step": 0.1},
    "Trihalomethanes": {"min": 0.0, "max": 300.0, "default": 66.3, "step": 1.0},
    "Turbidity": {"min": 0.0, "max": 20.0, "default": 3.96, "step": 0.1},
}

WHO_STANDARDS: Dict[str, Dict[str, Any]] = {
    "ph": {"unit": "", "desc": "WHO target pH is 6.5–8.5"},
    "Hardness": {"unit": "mg/L", "desc": "Desirable < 200 mg/L"},
    "Solids": {"unit": "ppm", "desc": "WHO desirable < 500 ppm"},
    "Chloramines": {"unit": "ppm", "desc": "EPA threshold <= 4.0 ppm"},
    "Sulfate": {"unit": "mg/L", "desc": "WHO guideline <= 250 mg/L"},
    "Conductivity": {"unit": "μS/cm", "desc": "Fresh water range 200–800 μS/cm"},
    "Organic_carbon": {"unit": "ppm", "desc": "Low TOC < 2.0 ppm is optimal"},
    "Trihalomethanes": {"unit": "μg/L", "desc": "EPA limit <= 80 μg/L"},
    "Turbidity": {"unit": "NTU", "desc": "WHO ideal < 1.0 NTU for drinking"},
}


def record_to_feature_dict(rec: Dict[str, Any]) -> Dict[str, float]:
    """Extract standard feature dictionary from SQLite database prediction row record."""
    return {
        "ph": rec.get("ph", 7.2),
        "Hardness": rec.get("hardness", 196.3),
        "Solids": rec.get("solids", 14200.0),
        "Chloramines": rec.get("chloramines", 7.13),
        "Sulfate": rec.get("sulfate", 333.0),
        "Conductivity": rec.get("conductivity", 421.0),
        "Organic_carbon": rec.get("organic_carbon", 14.1),
        "Trihalomethanes": rec.get("trihalomethanes", 66.3),
        "Turbidity": rec.get("turbidity", 3.96),
    }
