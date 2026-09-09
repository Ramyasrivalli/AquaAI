"""
auth.py — User Authentication, Password Hashing, & Security Question Password Reset.
"""

from typing import Optional, Tuple
from werkzeug.security import check_password_hash, generate_password_hash

from core.database import get_db_cursor, init_db
from core.validation import validate_credentials, validate_gmail


def hash_string(secret: str) -> str:
    """Hash string securely using PBKDF2 algorithm."""
    return generate_password_hash(secret.strip())


def verify_string(secret: str, stored_hash: str) -> bool:
    """Check string against stored password hash or fallback plaintext."""
    if not stored_hash:
        return False
    # If stored_hash is a pbkdf2 hash
    if stored_hash.startswith("pbkdf2:") or stored_hash.startswith("scrypt:"):
        return check_password_hash(stored_hash, secret.strip())
    # Backward-compatibility fallback for plaintext legacy dev records
    return secret.strip().lower() == stored_hash.strip().lower()


def register_user(
    email: str,
    password: str,
    security_question: str = "What is your favorite color?",
    security_answer: str = "blue",
) -> Tuple[bool, str]:
    """Register new user account with strict Gmail email validation."""
    clean_email = email.strip().lower()

    is_valid, msg = validate_credentials(clean_email, password)
    if not is_valid:
        return False, msg

    pwd_hash = hash_string(password)
    ans_hash = hash_string(security_answer.strip().lower())

    try:
        init_db()
        with get_db_cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (username, email, password_hash, security_question, security_answer_hash)
                VALUES (?, ?, ?, ?, ?)
                """,
                (clean_email, clean_email, pwd_hash, security_question.strip(), ans_hash),
            )
        return True, "Account registered successfully."
    except Exception as err:
        if "UNIQUE" in str(err):
            return False, f"Account '{clean_email}' is already registered. Please log in instead."
        return False, f"Registration failed: {err}"


def authenticate_user(email: str, password: str) -> Tuple[Optional[dict], str]:
    """Authenticate user credentials against SQLite database."""
    init_db()
    clean_email = email.strip().lower()

    is_valid, msg = validate_gmail(clean_email)
    if not is_valid:
        return None, msg

    if not password:
        return None, "Password is required."

    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM users WHERE LOWER(username) = ? OR LOWER(email) = ?", (clean_email, clean_email))
            user_row = cur.fetchone()
    except Exception as err:
        return None, f"Database connection error: {err}"

    if not user_row:
        return None, f"No registered account found for '{clean_email}'."

    if not check_password_hash(user_row["password_hash"], password.strip()):
        return None, "Incorrect password. Please verify your credentials and try again."

    user_dict = {
        "id": user_row["id"],
        "username": user_row["email"] or user_row["username"],
        "email": user_row["email"] or user_row["username"],
        "created_at": user_row["created_at"],
    }
    return user_dict, "Login successful!"


def get_user_security_question(email: str) -> Tuple[bool, str]:
    """Retrieve security question for registered Gmail account."""
    init_db()
    clean_email = email.strip().lower()

    is_valid, msg = validate_gmail(clean_email)
    if not is_valid:
        return False, msg

    with get_db_cursor() as cur:
        cur.execute(
            "SELECT security_question FROM users WHERE LOWER(username) = ? OR LOWER(email) = ?",
            (clean_email, clean_email),
        )
        row = cur.fetchone()

    if not row:
        return False, "Account not found. Please check your Gmail address."

    question = row["security_question"] or "What is your favorite color?"
    return True, question


def verify_security_answer(email: str, security_answer: str) -> Tuple[bool, str]:
    """Verify security answer against stored hash."""
    clean_email = email.strip().lower()
    clean_answer = security_answer.strip().lower()

    if not clean_email or not clean_answer:
        return False, "Gmail address and security answer are required."

    init_db()
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT id, security_answer_hash FROM users WHERE LOWER(username) = ? OR LOWER(email) = ?",
            (clean_email, clean_email),
        )
        user_row = cur.fetchone()

    if not user_row:
        return False, "Account not found. Please check your Gmail address."

    stored_ans_hash = user_row["security_answer_hash"]
    if not verify_string(clean_answer, stored_ans_hash):
        return False, "Incorrect security answer. Please try again."

    return True, "Identity verified successfully."


def update_user_password(email: str, new_password: str) -> Tuple[bool, str]:
    """Update password for verified user account."""
    clean_email = email.strip().lower()
    if not clean_email:
        return False, "Gmail address is required."
    if not new_password or len(new_password) < 4:
        return False, "New password must be at least 4 characters long."

    init_db()
    with get_db_cursor() as cur:
        cur.execute("SELECT id FROM users WHERE LOWER(username) = ? OR LOWER(email) = ?", (clean_email, clean_email))
        row = cur.fetchone()

    if not row:
        return False, f"Account '{clean_email}' not found."

    new_pwd_hash = hash_string(new_password)
    with get_db_cursor() as cur:
        cur.execute(
            "UPDATE users SET password_hash = ? WHERE LOWER(username) = ? OR LOWER(email) = ?",
            (new_pwd_hash, clean_email, clean_email),
        )

    return True, "Password reset successfully."
