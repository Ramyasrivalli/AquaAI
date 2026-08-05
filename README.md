# 💧 AquaAI — Water Quality Monitoring System

A production-quality Flask web application for evaluating drinking water potability, computing deterministic Water Quality Scores (0–100), diagnosing WHO/EPA parameter safety, generating actionable treatment recommendations, and exporting printable laboratory PDF reports.

---

## 📁 Project Architecture

```
water_prob_ai/
│
├── assets/                     # Project datasets & assets
│   └── water_potability.csv
│
├── config/                     # Application configuration
│   └── settings.py
│
├── core/                       # Core business logic & engines
│   ├── __init__.py
│   ├── auth.py                 # PBKDF2 password hashing & authentication
│   ├── database.py             # SQLite database operations & context managers
│   ├── helpers.py              # Configuration constants & data schemas
│   ├── prediction.py           # ML inference engine & deterministic scoring
│   ├── report.py               # ReportLab PDF laboratory report generator
│   └── validation.py           # Input range & credential validators
│
├── deployment/                 # Docker deployment assets
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── models/                     # Serialized ML artifacts
│   ├── best_model.pkl          # Serialized classifier model
│   ├── scaler.pkl              # Fitted StandardScaler
│   ├── imputer.pkl             # Fitted SimpleImputer
│   └── model_meta.json         # Evaluation metrics & metadata
│
├── notebook/                   # Development notebook reference
│   └── water_quality.ipynb
│
├── static/                     # CSS, JS, and static assets
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   ├── images/
│   ├── icons/
│   └── reports/
│
├── templates/                  # Jinja2 HTML templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── prediction.html
│   ├── analytics.html
│   ├── history.html
│   └── about.html
│
├── app.py                      # Flask Application Entry Point
├── train.py                    # Offline ML Model Training Script
├── requirements.txt            # Python Dependencies
├── README.md                   # System Documentation
├── .gitignore                  # Git Ignore Rules
└── water_quality.db            # SQLite Database
```

---

## 🚀 Setup & Execution

### 1. Local Run

```bash
# Install dependencies
pip install -r requirements.txt

# Launch Flask Application
python app.py
```

Access the application in your browser at:
`http://localhost:5050` (or `http://127.0.0.1:5050`)

---

## 🐳 Docker Deployment

```bash
# Launch container using Docker Compose
docker compose -f deployment/docker-compose.yml up --build -d
```

Access at `http://localhost:5050`.
