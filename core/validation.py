"""
validation.py — Parameter & Credential Validation Logic.
"""

import re
from typing import Dict, Tuple
from core.helpers import FEATURE_COLS, VALIDATION_RANGES


def parse_form_features(form_data: Dict[str, str]) -> Dict[str, float]:
    """Parse HTTP request form fields into float feature values with safe default fallback."""
    form_values = {}
    for col in FEATURE_COLS:
        val_str = form_data.get(col, "")
        try:
            form_values[col] = float(val_str)
        except (ValueError, TypeError):
            form_values[col] = VALIDATION_RANGES[col]["default"]
    return form_values


def validate_credentials(username: str, password: str) -> Tuple[bool, str]:
    """Validate user credential formatting (supports emails or usernames)."""
    user = username.strip().lower()
    if not user:
        return False, "Username or email is required."

    if len(user) < 3 or len(user) > 100:
        return False, "Username/email must be between 3 and 100 characters."

    is_email = "@" in user
    if is_email:
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, user):
            return False, "Invalid email format. Please enter a valid email address (e.g., user@example.com)."
    else:
        if not re.match(r"^[a-zA-Z0-9_.]+$", user):
            return False, "Username may only contain letters, numbers, underscores, and dots."

    if not password or len(password) < 4:
        return False, "Password must be at least 4 characters long."

    return True, ""
