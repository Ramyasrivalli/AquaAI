# AquaAI — Machine Learning Drinking Water Quality Assessment Platform

AquaAI is a production-quality, end-to-end AI/ML-powered drinking-water quality assessment platform designed to predict water potability, compute deterministic 0–100 Water Quality Scores (WQS), explain predictions via Explainable AI (SHAP), simulate parameter adjustments in real time, compare samples, process bulk CSV datasets, and generate laboratory PDF reports.

---

## Table of Contents
1. [Overview](#overview)
2. [Problem Statement](#problem-statement)
3. [Objectives](#objectives)
4. [Key Features](#key-features)
5. [Technology Stack](#technology-stack)
6. [Architecture](#architecture)
7. [ML Pipeline](#ml-pipeline)
8. [Dataset](#dataset)
9. [Input Parameters](#input-parameters)
10. [Water Quality Score Explanation](#water-quality-score-explanation)
11. [Explainable AI (SHAP)](#explainable-ai-shap)
12. [Recommendation Engine](#recommendation-engine)
13. [What-If Simulator](#what-if-simulator)
14. [Compare Feature](#compare-feature)
15. [Batch CSV Predictions](#batch-csv-predictions)
16. [Audit History](#audit-history)
17. [Analytics & Insights](#analytics--insights)
18. [PDF Laboratory Reports](#pdf-laboratory-reports)
19. [Authentication & Security](#authentication--security)
20. [Project Structure](#project-structure)
21. [Installation](#installation)
22. [Environment Variables](#environment-variables)
23. [Running Locally](#running-locally)
24. [Training the Model](#training-the-model)
25. [Testing](#testing)
26. [Manual Render Deployment](#manual-render-deployment)
27. [Limitations](#limitations)
28. [Future Improvements](#future-improvements)

---

## Overview
AquaAI provides water safety intelligence for municipal, industrial, agricultural, and residential water quality management. By combining pre-trained scikit-learn machine learning classification models with WHO/EPA domain rules and SHAP feature attributions, AquaAI transforms raw water parameter values into actionable safety decisions.

## Problem Statement
Access to clean drinking water is vital for human health. Traditional physical and chemical testing requires specialized lab interpretation to evaluate complex non-linear interactions across multiple parameters (e.g., pH, Total Dissolved Solids, Heavy Chloramines, Trihalomethanes, Turbidity). AquaAI automates instant potability evaluation and provides clear treatment guidance.

## Objectives
- Automate potability classification (Safe / Unsafe).
- Compute a standardized 0–100 Water Quality Score (WQS) based on WHO guidelines.
- Provide Explainable AI (SHAP) attributions to identify key risk drivers.
- Provide real-time "What-If" parameter simulation and side-by-side sample comparison.
- Enable batch CSV ingestion and downloadable PDF certificates.

## Key Features
- **Strict Gmail Authentication**: Secure registration and login enforcing `@gmail.com` addresses.
- **Security Question Password Reset**: Multi-step identity verification via registered Security Question & PBKDF2 hashed Security Answer with server-side session protection and attempt rate limiting (no SMTP or external email services required).
- **Primary Water Analysis Workspace**: Compact 2–4 column input form with unit labels, WHO reference ranges, and numerical validation.
- **Explainable AI (SHAP)**: Identifies top influential parameters driving ML potability predictions.
- **What-If Parameter Simulator**: Interactive sliders for instant "what-if" treatment recalculations.
- **Side-by-Side Sample Comparison**: Compare Sample A vs Sample B metrics, potability, and scores on a single screen.
- **Batch CSV Predictions**: Upload CSV datasets, validate schema, run ML inference across all rows, and download results.
- **Audit History**: User-isolated log to inspect, filter, search, and export past predictions.
- **Database Analytics**: Dynamic charts (Chart.js) and statistical summary tables generated directly from SQLite history.
- **ReportLab PDF Reports**: Professional downloadable laboratory quality certificates.

## Technology Stack
- **Backend Framework**: Python 3.10+, Flask 3.0+
- **Production Web Server**: Gunicorn
- **Machine Learning & Data**: scikit-learn, pandas, numpy, joblib, SHAP
- **Database**: SQLite3 (with row factory & context management)
- **PDF Generation**: ReportLab
- **Frontend / UI**: HTML5, CSS3 (Custom Aqua Theme), Bootstrap 5, FontAwesome 6, Chart.js

## Architecture
```
[ User Web Browser ]
        │
        ▼ (HTTP / REST API)
┌─────────────────────────────────────────────────────────┐
│                      Flask Application                  │
│  (Auth, Analysis, Simulator, Compare, Batch, Analytics) │
└───────────┬─────────────────────────┬───────────────────┘
            │                         │
            ▼                         ▼
┌─────────────────────────┐ ┌─────────────────────────────┐
│    SQLite Database      │ │      Core ML Engine         │
│  (users & predictions)  │ │(scaler, imputer, best_model)│
└─────────────────────────┘ └──────────────┬──────────────┘
                                           │
                                           ▼
                                  ┌──────────────────┐
                                  │ SHAP Explainable │
                                  │   AI & WQS Rules │
                                  └──────────────────┘
```

## ML Pipeline
1. **Input**: 9 physical/chemical water quality parameters.
2. **Imputation**: Median imputer (`imputer.pkl`).
3. **Scaling**: Standard Scaler (`scaler.pkl`).
4. **Inference**: Pre-trained model (`best_model.pkl`, Support Vector Machine).
5. **Output**: Binary Potability Prediction (0 = Unsafe, 1 = Safe) + Calibrated Probability Confidence.

## Dataset
Trained on the standard **Water Potability Dataset** (`assets/water_potability.csv`), containing 3,276 water body samples.

## Input Parameters
1. **pH Level**: Acidic / Alkaline balance (WHO range: 6.5–8.5).
2. **Hardness**: Dissolved calcium and magnesium salts (mg/L).
3. **Solids (TDS)**: Total Dissolved Solids in parts per million (ppm).
4. **Chloramines**: Primary disinfectant concentration (ppm).
5. **Sulfate**: Dissolved sulfate minerals (mg/L).
6. **Conductivity**: Electrical conductivity (μS/cm).
7. **Organic Carbon (TOC)**: Total organic carbon content (ppm).
8. **Trihalomethanes (THM)**: Disinfectant byproduct concentration (μg/L).
9. **Turbidity**: Measure of water clarity/cloudiness (NTU).

## Water Quality Score Explanation
The Water Quality Score (WQS) is a deterministic 0–100 metric calculated by penalizing deviations from established WHO/EPA drinking guidelines:
- **85 – 100**: Excellent Quality
- **70 – 84**: Good Quality
- **50 – 69**: Fair Quality
- **30 – 49**: Poor Quality
- **0 – 29**: Very Poor Quality

## Explainable AI (SHAP)
Explains *why* the model predicted a sample as potable or non-potable by calculating feature attributions (SHAP values / model sensitivity attributions) and displaying relative influence percentages for each parameter.

## Recommendation Engine
Generates dynamic, rule-based treatment recommendations based on detected parameter abnormalities (e.g., Reverse Osmosis for high TDS, Alkaline Neutralization for acidic pH, Pack-Tower Air Stripping for high THM). Includes standard disclaimer that AquaAI is a decision support tool and does not replace certified lab testing.

## What-If Simulator
Located at `/simulator`. Features 9 interactive range sliders to adjust parameter values and instantly observe live changes in potability prediction, WQS, parameter status, and treatment recommendations without page reloads.

## Compare Feature
Located at `/compare`. Allows side-by-side comparison of Sample A vs Sample B parameters, potability verdicts, quality scores, and risk factors in a single desktop screen view.

## Batch CSV Predictions
Located at `/batch`. Enables uploading a CSV file containing water quality parameters. The app validates required columns, executes ML inference across all rows, displays summary statistics, and provides a CSV export download.

## Audit History
Located at `/history`. Displays user-isolated historical prediction records with search, filtering, detailed inspection, CSV export, and PDF generation.

## Analytics & Insights
Located at `/analytics`. Renders interactive Chart.js visualizations (potability pie charts, historical score trends, pH/TDS distribution lines) and descriptive statistical summary tables computed directly from database history. Displays a clear empty-state message when no historical records exist.

## PDF Laboratory Reports
Generates downloadable, official ReportLab PDF quality certificates containing AquaAI branding, metadata, verdict banner, parameter diagnostic tables, AI recommendations, and suitable application categories.

## Authentication & Security
- **Gmail-Only Enforcement**: Frontend and backend regex validation (`@gmail.com`).
- **Password Protection**: Hashed using Werkzeug PBKDF2 algorithm.
- **Security Question Password Reset**: Multi-step verification using registered Security Question & PBKDF2 hashed Security Answer. Server-side session verification (`reset_verified = True`) with a 5-attempt limit prevents brute-force guessing and unauthorized access.
- **Data Isolation**: Database queries strictly filter records by authenticated `user_id`.

## Project Structure
```
AquaAI/
│
├── app.py                  # Main Flask application entry point & route handlers
├── train.py                # Offline ML model training & serialization script
├── requirements.txt        # Python package dependencies
├── README.md               # Project documentation
├── .gitignore              # Git version control exclusions
├── .env.example            # Environment variables configuration template
│
├── assets/
│   └── water_potability.csv # Historical dataset
│
├── models/
│   ├── best_model.pkl      # Trained ML classification model
│   ├── scaler.pkl          # Trained StandardScaler
│   ├── imputer.pkl         # Trained SimpleImputer
│   └── model_meta.json     # Model metrics and feature metadata
│
├── core/
│   ├── __init__.py         # Core package exports
│   ├── auth.py             # User registration, authentication, & security question reset
│   ├── database.py         # SQLite schema & query operations
│   ├── explainability.py   # SHAP Explainable AI attribution engine
│   ├── helpers.py          # Validation ranges & WHO standards
│   ├── prediction.py       # ML inference, WQS calculation, & recommendation engine
│   ├── report.py           # ReportLab PDF certificate generator
│   └── validation.py       # Gmail & numeric parameter validation
│
├── templates/
│   ├── base.html           # Base layout template with sticky navbar
│   ├── login.html          # Tabbed login, register modal, & Security Question reset UI
│   ├── analysis.html       # Primary Water Quality Analysis workspace
│   ├── simulator.html      # Interactive What-If Simulator
│   ├── compare.html        # Side-by-side Sample Comparison
│   ├── batch.html          # Batch CSV upload & processing
│   ├── history.html        # Audit history log
│   └── analytics.html      # Database statistics & Chart.js visual analytics
│
└── static/
    ├── css/
    │   └── style.css       # AquaAI design tokens & modular stylesheet
    └── js/
        └── main.js         # Frontend interactions, Security Question reset flow, & form validation
```

## Installation
1. **Clone the repository**:
   ```bash
   git clone https://github.com/Ramyasrivalli/AquaAI.git
   cd AquaAI
   ```
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Environment Variables
Copy `.env.example` to `.env` and fill in your configuration:
```env
SECRET_KEY=your_production_secret_key
FLASK_PORT=5050
FLASK_DEBUG=False
DB_PATH=water_quality.db
```

## Running Locally
Start the Flask application:
```bash
python app.py
```
Open your browser and navigate to `http://localhost:5050`.

## Training the Model
To re-train the ML models on updated dataset files:
```bash
python train.py
```

## Testing
Run automated unit compilation and end-to-end verification checks:
```bash
python -m py_compile app.py train.py core/*.py config/*.py
```

## Manual Render Deployment
To manually deploy AquaAI on Render:
- **Environment**: Python 3.10+
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Environment Variables**: Set `SECRET_KEY`, `FLASK_DEBUG=False`.

*Note: Render's default filesystem is ephemeral. Runtime SQLite database records may reset across service restarts.*

## Limitations
- AquaAI is an AI decision-support platform and does not replace certified laboratory chemical testing.

## Future Improvements
- Multi-language support for global water quality monitoring.
- Geographic GIS mapping of water potability scores.
- Support for PostgreSQL database storage for persistent cloud deployments.
