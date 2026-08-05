"""
auth.py — User Authentication, Password Hashing, & Local Password Reset.
"""

from typing import Optional, Tuple
from werkzeug.security import check_password_hash, generate_password_hash

from core.database import get_db_cursor, init_db
from core.validation import validate_credentials


def hash_string(secret: str) -> str:
    """Hash string securely using Werkzeug default PBKDF2 algorithm."""
    return generate_password_hash(secret.strip())


def verify_string(secret: str, stored_hash: str) -> bool:
    """Check string against stored Werkzeug password hash."""
    if not stored_hash:
        return False
    return check_password_hash(stored_hash, secret.strip())


def register_user(
    username: str,
    password: str,
    security_question: str = "What is your favorite color?",
    security_answer: str = "blue",
) -> Tuple[bool, str]:
    """Register new user account with hashed password and security answer."""
    is_valid, msg = validate_credentials(username, password)
    if not is_valid:
        return False, msg

    clean_user = username.strip().lower()
    pwd_hash = hash_string(password)
    ans_hash = hash_string(security_answer.strip().lower())

    try:
        init_db()
        with get_db_cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (username, password_hash, security_question, security_answer_hash)
                VALUES (?, ?, ?, ?)
                """,
                (clean_user, pwd_hash, security_question.strip(), ans_hash),
            )
        return True, "Registration successful! Please log in with your credentials."
    except Exception as err:
        if "UNIQUE" in str(err):
            return False, f"Account '{clean_user}' is already registered. Please log in instead."
        return False, f"Registration failed: {err}"


def authenticate_user(username: str, password: str) -> Tuple[Optional[dict], str]:
    """Authenticate user credentials against SQLite database with detailed feedback."""
    init_db()
    clean_user = username.strip().lower()
    if not clean_user:
        return None, "Email address or username is required."
    if not password:
        return None, "Password is required."

    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = ?", (clean_user,))
            user_row = cur.fetchone()
    except Exception as err:
        return None, f"Database connection error: {err}"

    if not user_row:
        return None, f"No account found for '{clean_user}'. Please check your spelling or register a new account."

    if not verify_string(password, user_row["password_hash"]):
        return None, "Incorrect password. Please verify your password and try again."

    user_dict = {
        "id": user_row["id"],
        "username": user_row["username"],
        "security_question": user_row["security_question"] or "What is your favorite color?",
        "created_at": user_row["created_at"],
    }
    return user_dict, "Login successful!"


def get_security_question(username: str) -> Optional[str]:
    """Retrieve security question for a registered user."""
    init_db()
    clean_user = username.strip().lower()
    with get_db_cursor() as cur:
        cur.execute("SELECT security_question FROM users WHERE username = ?", (clean_user,))
        row = cur.fetchone()
        if row and row["security_question"]:
            return row["security_question"]
        elif row:
            return "What is your favorite color?"
        return None


def reset_password_with_security_answer(
    username: str, security_answer: str, new_password: str
) -> Tuple[bool, str]:
    """Reset user password using local security answer verification."""
    clean_user = username.strip().lower()
    if not username:
        return False, "Account email or username is required."
    if not new_password or len(new_password) < 4:
        return False, "New password must be at least 4 characters long."

    init_db()
    with get_db_cursor() as cur:
        cur.execute("SELECT id, security_answer_hash FROM users WHERE username = ?", (clean_user,))
        user_row = cur.fetchone()

    if not user_row:
        return False, f"Account '{clean_user}' not found. Please check your username/email."

    stored_ans_hash = user_row["security_answer_hash"]
    if stored_ans_hash and not verify_string(security_answer.strip().lower(), stored_ans_hash):
        return False, "Incorrect security answer. Password reset failed."

    new_pwd_hash = hash_string(new_password)
    with get_db_cursor() as cur:
        cur.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (new_pwd_hash, clean_user),
        )

    return True, "Password reset successful! Please log in with your new password."
