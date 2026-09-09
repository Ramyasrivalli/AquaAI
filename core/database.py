"""
database.py — Centralized SQLite Database Operations & Schema Management.
"""

import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional
import pandas as pd
from config.settings import DB_PATH


def get_connection() -> sqlite3.Connection:
    """Return an SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db_cursor() -> Generator[sqlite3.Cursor, None, None]:
    """Context manager for SQLite transactions with automatic commit/rollback."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Initialize SQLite database schema and perform safe column migrations."""
    with get_db_cursor() as cur:
        # Users Table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id                     INTEGER PRIMARY KEY AUTOINCREMENT,
                username               TEXT UNIQUE NOT NULL,
                email                  TEXT UNIQUE,
                password_hash          TEXT NOT NULL,
                security_question      TEXT,
                security_answer_hash   TEXT,
                created_at             DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Predictions Table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL,
                ph              REAL,
                hardness        REAL,
                solids          REAL,
                chloramines     REAL,
                sulfate         REAL,
                conductivity    REAL,
                organic_carbon  REAL,
                trihalomethanes REAL,
                turbidity       REAL,
                result          INTEGER NOT NULL,
                confidence      REAL NOT NULL,
                quality_score   REAL NOT NULL,
                quality_status  TEXT NOT NULL,
                model_used      TEXT,
                created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
            """
        )

        # Safe Column Migrations for users table
        cur.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cur.fetchall()]
        if "email" not in columns:
            cur.execute("ALTER TABLE users ADD COLUMN email TEXT")
        if "security_question" not in columns:
            cur.execute("ALTER TABLE users ADD COLUMN security_question TEXT")
        if "security_answer_hash" not in columns:
            cur.execute("ALTER TABLE users ADD COLUMN security_answer_hash TEXT")


def save_prediction(
    user_id: int,
    feature_dict: Dict[str, float],
    result: int,
    confidence: float,
    quality_score: float,
    quality_status: str,
    model_used: str,
) -> int:
    """Save prediction record to SQLite."""
    init_db()
    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO predictions (
                user_id, ph, hardness, solids, chloramines, sulfate,
                conductivity, organic_carbon, trihalomethanes, turbidity,
                result, confidence, quality_score, quality_status, model_used
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                feature_dict.get("ph"),
                feature_dict.get("Hardness"),
                feature_dict.get("Solids"),
                feature_dict.get("Chloramines"),
                feature_dict.get("Sulfate"),
                feature_dict.get("Conductivity"),
                feature_dict.get("Organic_carbon"),
                feature_dict.get("Trihalomethanes"),
                feature_dict.get("Turbidity"),
                result,
                confidence,
                quality_score,
                quality_status,
                model_used,
            ),
        )
        return cur.lastrowid


def get_user_predictions(user_id: int, limit: int = 500) -> List[Dict[str, Any]]:
    """Fetch user prediction records isolated strictly by user_id."""
    init_db()
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT * FROM predictions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        )
        return [dict(r) for r in cur.fetchall()]


def get_prediction_by_id(pred_id: int) -> Optional[Dict[str, Any]]:
    """Fetch single prediction record by primary key."""
    init_db()
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM predictions WHERE id = ?", (pred_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def delete_prediction(pred_id: int, user_id: int) -> bool:
    """Delete a prediction record for a given user."""
    init_db()
    with get_db_cursor() as cur:
        cur.execute("DELETE FROM predictions WHERE id = ? AND user_id = ?", (pred_id, user_id))
        return cur.rowcount > 0


def get_summary_stats(user_id: Optional[int] = None) -> Dict[str, Any]:
    """Compute aggregate analytics statistics dynamically from database records."""
    init_db()
    with get_db_cursor() as cur:
        where = " WHERE user_id = ?" if user_id else ""
        params = (user_id,) if user_id else ()

        cur.execute(
            f"""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN result = 1 THEN 1 ELSE 0 END) as safe,
                AVG(quality_score) as avg_score,
                AVG(confidence) as avg_conf
            FROM predictions{where}
            """,
            params,
        )
        row = cur.fetchone()
        total = row["total"] or 0
        safe = row["safe"] or 0
        avg_score = row["avg_score"] or 0.0
        avg_conf = row["avg_conf"] or 0.0

    unsafe = total - safe
    potable_pct = round((safe / total * 100.0), 1) if total > 0 else 0.0
    return {
        "total_tests": total,
        "potable_count": safe,
        "non_potable_count": unsafe,
        "potable_percentage": potable_pct,
        "avg_quality_score": round(float(avg_score), 1),
        "avg_confidence_pct": round(float(avg_conf * 100.0), 1),
    }


def get_predictions_df(user_id: Optional[int] = None) -> pd.DataFrame:
    """Return historical predictions DataFrame."""
    init_db()
    conn = get_connection()
    query = (
        "SELECT * FROM predictions WHERE user_id = ? ORDER BY created_at ASC"
        if user_id
        else "SELECT * FROM predictions ORDER BY created_at ASC"
    )
    df = pd.read_sql_query(query, conn, params=(user_id,) if user_id else ())
    conn.close()
    return df


def get_analytics_summary(user_id: int) -> Dict[str, Any]:
    """Compute statistical parameter summaries and chart metrics for analytics dashboard."""
    df = get_predictions_df(user_id=user_id)
    chart_dates = []
    scores = []
    ph_values = []
    solids_values = []
    potable_count = 0
    non_potable_count = 0
    stats_table = []

    if not df.empty:
        chart_dates = df["created_at"].astype(str).tolist()
        scores = df["quality_score"].tolist()
        ph_values = df["ph"].tolist()
        solids_values = df["solids"].tolist()

        potable_count = int((df["result"] == 1).sum())
        non_potable_count = int((df["result"] == 0).sum())

        num_cols = ["ph", "hardness", "solids", "chloramines", "sulfate", "conductivity", "organic_carbon", "trihalomethanes", "turbidity", "quality_score"]
        desc = df[num_cols].describe().T.reset_index()
        for _, row in desc.iterrows():
            stats_table.append({
                "parameter": row["index"],
                "mean": row["mean"],
                "std": row["std"],
                "min": row["min"],
                "25%": row["25%"],
                "50%": row["50%"],
                "75%": row["75%"],
                "max": row["max"],
            })

    return {
        "chart_dates": chart_dates,
        "scores": scores,
        "ph_values": ph_values,
        "solids_values": solids_values,
        "potable_count": potable_count,
        "non_potable_count": non_potable_count,
        "stats_table": stats_table,
    }
