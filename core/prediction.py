"""
prediction.py — Machine Learning Inference Engine, Diagnostic Evaluator, & Recommendation Logic.
"""

from dataclasses import asdict, dataclass
import json
import joblib
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple

from core.database import save_prediction
from core.explainability import compute_feature_explanations
from core.helpers import (
    FEATURE_COLS,
    FEATURE_LABELS,
    FEATURE_UNITS,
    IMPUTER_PATH,
    META_PATH,
    MODEL_PATH,
    SCALER_PATH,
    WHO_STANDARDS,
)

# Module-level memory cache for loaded ML artifacts
_MODEL = None
_SCALER = None
_IMPUTER = None
_META = None
_MODEL_NAME = "Support Vector Machine"


def load_artifacts() -> bool:
    """Load machine learning model artifacts into memory once on application startup."""
    global _MODEL, _SCALER, _IMPUTER, _META, _MODEL_NAME
    if _MODEL is not None:
        return True

    try:
        if MODEL_PATH.exists():
            _MODEL = joblib.load(MODEL_PATH)
        if SCALER_PATH.exists():
            _SCALER = joblib.load(SCALER_PATH)
        if IMPUTER_PATH.exists():
            _IMPUTER = joblib.load(IMPUTER_PATH)
        if META_PATH.exists():
            with open(META_PATH, "r") as f:
                _META = json.load(f)
                _MODEL_NAME = _META.get("best_model_name", "Support Vector Machine")
        return True
    except Exception as err:
        print(f"[ERROR] Failed to load ML artifacts: {err}")
        return False


def get_model_name() -> str:
    """Return active model name."""
    load_artifacts()
    return _MODEL_NAME


def get_model_meta() -> dict:
    """Return model evaluation metadata."""
    load_artifacts()
    return _META or {}


@dataclass
class ParameterEval:
    key: str
    label: str
    value: float
    unit: str
    reference: str
    status: str  # 'Ideal', 'Abnormal', 'Unsafe'
    recommendation: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AnalysisResult:
    is_potable: bool
    confidence: float
    confidence_pct: float
    quality_score: float
    quality_status: str
    parameter_evaluations: List[dict]
    recommendations: List[str]
    suitable_uses: List[str]
    model_used: str
    feature_explanations: List[dict]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AnalysisResult":
        return cls(**data)


def compute_water_quality_score(features: Dict[str, Any]) -> Tuple[float, str]:
    """Compute a deterministic 0–100 Water Quality Score based on WHO deviation penalties."""
    score = 100.0
    penalties = 0.0

    def get_num(key: str, default: float) -> float:
        try:
            return float(features.get(key, default))
        except (ValueError, TypeError):
            return default

    ph = get_num("ph", 7.0)
    if ph < 6.5 or ph > 8.5:
        penalties += min(30.0, abs(ph - 7.5) * 15.0)

    hardness = get_num("Hardness", 150.0)
    if hardness > 200.0:
        penalties += min(20.0, (hardness - 200.0) / 15.0)

    tds = get_num("Solids", 500.0)
    if tds > 500.0:
        penalties += min(25.0, (tds - 500.0) / 500.0)

    chloramines = get_num("Chloramines", 2.0)
    if chloramines > 4.0:
        penalties += min(20.0, (chloramines - 4.0) * 5.0)

    sulfate = get_num("Sulfate", 200.0)
    if sulfate > 250.0:
        penalties += min(20.0, (sulfate - 250.0) / 10.0)

    organic_carbon = get_num("Organic_carbon", 1.0)
    if organic_carbon > 2.0:
        penalties += min(20.0, (organic_carbon - 2.0) * 3.0)

    thm = get_num("Trihalomethanes", 50.0)
    if thm > 80.0:
        penalties += min(20.0, (thm - 80.0) / 3.0)

    turbidity = get_num("Turbidity", 1.0)
    if turbidity > 1.0:
        penalties += min(20.0, (turbidity - 1.0) * 8.0)

    final_score = max(0.0, min(100.0, round(score - penalties, 1)))

    if final_score >= 85:
        status = "Excellent"
    elif final_score >= 70:
        status = "Good"
    elif final_score >= 50:
        status = "Fair"
    elif final_score >= 30:
        status = "Poor"
    else:
        status = "Very Poor"

    return final_score, status


def evaluate_parameters(features: Dict[str, Any]) -> Tuple[List[dict], List[str], List[str]]:
    """Evaluate individual water parameters against WHO/EPA safety thresholds."""
    evaluations = []
    recommendations = []
    suitable_uses = []

    def get_num(key: str, default: float) -> float:
        try:
            return float(features.get(key, default))
        except (ValueError, TypeError):
            return default

    ph = get_num("ph", 7.0)
    if 6.5 <= ph <= 8.5:
        ph_status = "Ideal"
        ph_rec = "pH is within standard WHO drinking range."
    elif ph < 6.5:
        ph_status = "Abnormal (Acidic)"
        ph_rec = "Acidic water. Install alkaline neutralizing filter or soda ash dosing system."
        recommendations.append("Apply alkaline neutralization (soda ash or calcite filter) to correct acidic pH.")
    else:
        ph_status = "Abnormal (Alkaline)"
        ph_rec = "Alkaline water. Add food-grade acid injection system (e.g. citric/sulfuric acid dosing)."
        recommendations.append("Implement acid injection dosing system to lower elevated alkaline pH.")

    evaluations.append(ParameterEval("ph", "pH Level", ph, "", "6.5 – 8.5", ph_status, ph_rec).to_dict())

    hardness = get_num("Hardness", 150.0)
    if hardness <= 200.0:
        h_status = "Ideal"
        h_rec = "Hardness within desirable limits."
    elif hardness <= 300.0:
        h_status = "Abnormal (Moderately Hard)"
        h_rec = "Consider ion-exchange water softener to prevent boiler scale."
        recommendations.append("Install an ion-exchange water softener for mineral reduction.")
    else:
        h_status = "Unsafe (Very Hard)"
        h_rec = "High scaling potential. Install industrial sodium-cation exchange softener."
        recommendations.append("Deploy industrial sodium-cation exchange softener to prevent heavy pipe scaling.")

    evaluations.append(ParameterEval("Hardness", "Hardness", hardness, "mg/L", "< 200 mg/L", h_status, h_rec).to_dict())

    tds = get_num("Solids", 500.0)
    if tds <= 500.0:
        tds_status = "Ideal"
        tds_rec = "Total Dissolved Solids within desirable drinking limits."
    elif tds <= 1000.0:
        tds_status = "Abnormal (Elevated Solids)"
        tds_rec = "Install Reverse Osmosis (RO) or nanofiltration system."
        recommendations.append("Deploy Reverse Osmosis (RO) filtration system to reduce elevated Total Dissolved Solids.")
    else:
        tds_status = "Unsafe (High Salinity)"
        tds_rec = "High mineralization. Multi-stage Reverse Osmosis or electrodialysis required."
        recommendations.append("Multi-stage Reverse Osmosis (RO) desalting required before human consumption.")

    evaluations.append(ParameterEval("Solids", "TDS / Solids", tds, "ppm", "< 500 ppm", tds_status, tds_rec).to_dict())

    chloramines = get_num("Chloramines", 2.0)
    if chloramines <= 4.0:
        c_status = "Ideal"
        c_rec = "Chloramines concentration within EPA safe limits."
    else:
        c_status = "Abnormal (Elevated Disinfectant)"
        c_rec = "Install catalytic carbon filtration or sodium bisulfite dechlorination."
        recommendations.append("Deploy catalytic activated carbon filters for chloramine removal.")

    evaluations.append(ParameterEval("Chloramines", "Chloramines", chloramines, "ppm", "< 4.0 ppm", c_status, c_rec).to_dict())

    sulfate = get_num("Sulfate", 200.0)
    if sulfate <= 250.0:
        s_status = "Ideal"
        s_rec = "Sulfate level within WHO guidelines."
    else:
        s_status = "Abnormal (Elevated Sulfate)"
        s_rec = "May cause laxative effects. Install strong-base anion exchange resin."
        recommendations.append("Install strong-base anion exchange resin or RO for sulfate removal.")

    evaluations.append(ParameterEval("Sulfate", "Sulfate", sulfate, "mg/L", "< 250 mg/L", s_status, s_rec).to_dict())

    cond = get_num("Conductivity", 400.0)
    if cond <= 800.0:
        cond_status = "Ideal"
        cond_rec = "Conductivity normal for fresh water."
    else:
        cond_status = "Abnormal (High Electrical Conductivity)"
        cond_rec = "High dissolved ion content. Use deionization or RO process."
        recommendations.append("Apply deionization or reverse osmosis process for conductive ion reduction.")

    evaluations.append(ParameterEval("Conductivity", "Conductivity", cond, "μS/cm", "200 – 800 μS/cm", cond_status, cond_rec).to_dict())

    toc = get_num("Organic_carbon", 1.0)
    if toc <= 2.0:
        toc_status = "Ideal"
        toc_rec = "Organic carbon content low and desirable."
    else:
        toc_status = "Abnormal (Elevated Organics)"
        toc_rec = "Organics promote bacterial growth. Apply Granular Activated Carbon (GAC) filtration."
        recommendations.append("Use Granular Activated Carbon (GAC) or ozone-biological activated carbon treatment.")

    evaluations.append(ParameterEval("Organic_carbon", "Organic Carbon", toc, "ppm", "< 2.0 ppm", toc_status, toc_rec).to_dict())

    thm = get_num("Trihalomethanes", 50.0)
    if thm <= 80.0:
        thm_status = "Ideal"
        thm_rec = "Trihalomethanes within EPA disinfectant byproduct limits."
    else:
        thm_status = "Unsafe (High Carcinogenic Byproducts)"
        thm_rec = "Exceeds EPA limits. Implement air stripping or Advanced Oxidation Process (AOP)."
        recommendations.append("Apply packed-tower air stripping or UV/H2O2 Advanced Oxidation Process for THM removal.")

    evaluations.append(ParameterEval("Trihalomethanes", "Trihalomethanes", thm, "μg/L", "< 80 μg/L", thm_status, thm_rec).to_dict())

    turb = get_num("Turbidity", 1.0)
    if turb <= 1.0:
        turb_status = "Ideal"
        turb_rec = "Water clarity excellent."
    elif turb <= 5.0:
        turb_status = "Abnormal (Slightly Turbid)"
        turb_rec = "Install dual-media sand filter or 5-micron sediment filter."
        recommendations.append("Deploy 5-micron sediment filter cartridge or sand filter.")
    else:
        turb_status = "Unsafe (High Cloudiness)"
        turb_rec = "High particulate count. Implement chemical coagulation, flocculation, and ultrafiltration."
        recommendations.append("Apply alum coagulation, sedimentation, and ultrafiltration membrane treatment.")

    evaluations.append(ParameterEval("Turbidity", "Turbidity", turb, "NTU", "< 1.0 NTU", turb_status, turb_rec).to_dict())

    if len(recommendations) == 0:
        recommendations.append("Water parameters meet WHO standards. Maintain routine monitoring.")

    # Always append standard lab decision support disclaimer
    recommendations.append("Notice: AquaAI provides machine learning decision support and does not replace certified laboratory testing.")

    # Suitable applications determination
    if ph >= 6.5 and ph <= 8.5 and tds <= 500 and turb <= 1.0 and thm <= 80:
        suitable_uses.append("Direct Potable Human Drinking Water")
        suitable_uses.append("Food & Beverage Manufacturing")

    if tds <= 1000 and hardness <= 300:
        suitable_uses.append("Residential Sanitation & Bathing")
        suitable_uses.append("Agricultural Irrigation & Livestock")

    suitable_uses.append("Industrial Cooling Towers & Utility Operations")
    if not suitable_uses:
        suitable_uses.append("Non-potable Industrial Process Use Only")

    return evaluations, recommendations, suitable_uses


def run_inference(
    feature_dict: Dict[str, Any],
    user_id: Optional[int] = None,
    save_to_db: bool = True,
) -> Tuple[AnalysisResult, Optional[int]]:
    """Run machine learning model inference and return populated AnalysisResult object."""
    load_artifacts()

    # Convert dictionary values to float safely
    clean_dict = {}
    for col in FEATURE_COLS:
        try:
            clean_dict[col] = float(feature_dict.get(col, 0.0))
        except (ValueError, TypeError):
            clean_dict[col] = 0.0

    raw_vals = [clean_dict[col] for col in FEATURE_COLS]
    X_raw = np.array([raw_vals], dtype=float)

    # Preprocessing
    if _IMPUTER is not None:
        X_imp = _IMPUTER.transform(X_raw)
    else:
        X_imp = X_raw

    if _SCALER is not None:
        X_scaled = _SCALER.transform(X_imp)
    else:
        X_scaled = X_imp

    # Model Prediction
    if _MODEL is not None:
        pred_class = int(_MODEL.predict(X_scaled)[0])
        if hasattr(_MODEL, "predict_proba"):
            probs = _MODEL.predict_proba(X_scaled)[0]
            conf = float(probs[pred_class])
        elif hasattr(_MODEL, "decision_function"):
            df_val = float(_MODEL.decision_function(X_scaled)[0])
            conf = float(1.0 / (1.0 + np.exp(-abs(df_val))))
        else:
            conf = 0.75
    else:
        ph = clean_dict.get("ph", 7.0)
        tds = clean_dict.get("Solids", 500.0)
        pred_class = 1 if (6.5 <= ph <= 8.5 and tds <= 1000.0) else 0
        conf = 0.72

    conf_pct = round(conf * 100.0, 1)
    quality_score, quality_status = compute_water_quality_score(clean_dict)
    evaluations, recommendations, suitable_uses = evaluate_parameters(clean_dict)
    feature_explanations = compute_feature_explanations(_MODEL, _SCALER, _IMPUTER, clean_dict)

    result_obj = AnalysisResult(
        is_potable=bool(pred_class == 1),
        confidence=conf,
        confidence_pct=conf_pct,
        quality_score=quality_score,
        quality_status=quality_status,
        parameter_evaluations=evaluations,
        recommendations=recommendations,
        suitable_uses=suitable_uses,
        model_used=_MODEL_NAME,
        feature_explanations=feature_explanations,
    )

    record_id = None
    if save_to_db and user_id is not None:
        try:
            record_id = save_prediction(
                user_id=user_id,
                feature_dict=clean_dict,
                result=pred_class,
                confidence=conf,
                quality_score=quality_score,
                quality_status=quality_status,
                model_used=_MODEL_NAME,
            )
        except Exception as err:
            print(f"[WARNING] Could not save prediction record to database: {err}")

    return result_obj, record_id
