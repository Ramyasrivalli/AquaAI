"""
settings.py — Central Application Configuration & Environment Constants.
"""

from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
CORE_DIR = BASE_DIR / "core"
MODELS_DIR = BASE_DIR / "models"
ASSETS_DIR = BASE_DIR / "assets"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Sub-Static Paths
STATIC_IMAGES_DIR = STATIC_DIR / "images"
STATIC_ICONS_DIR = STATIC_DIR / "icons"
STATIC_REPORTS_DIR = STATIC_DIR / "reports"
STATIC_CSS_DIR = STATIC_DIR / "css"
STATIC_JS_DIR = STATIC_DIR / "js"

# Data & File Paths
DB_PATH = BASE_DIR / "water_quality.db"
CSV_PATH = ASSETS_DIR / "water_potability.csv"
MODEL_PATH = MODELS_DIR / "best_model.pkl"
SCALER_PATH = MODELS_DIR / "scaler.pkl"
IMPUTER_PATH = MODELS_DIR / "imputer.pkl"
META_PATH = MODELS_DIR / "model_meta.json"

# Flask Application Settings
SECRET_KEY = "aqua_ai_super_secret_production_key"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5050
DEBUG = True
