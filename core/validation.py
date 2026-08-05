"""
validation.py — Parameter & Credential Validation Logic.
"""

import math
import re
from typing import Dict, List, Tuple
from core.helpers import FEATURE_COLS, VALIDATION_RANGES


def validate_water_params(params: Dict[str, float]) -> Tuple[bool, List[str]]:
    """Validate parameter types, numerical limits, and NaN values."""
    errors = []
    for col in FEATURE_COLS:
        val = params.get(col)
        if val is None or not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
            errors.append(f"Invalid numerical value for '{col}'.")
            continue

        bounds = VALIDATION_RANGES.get(col, {})
        if val < bounds.get("min", 0.0) or val > bounds.get("max", 1e6):
            errors.append(f"Parameter '{col}' ({val}) is out of allowed range [{bounds['min']}, {bounds['max']}].")

    return len(errors) == 0, errors


def validate_credentials(username: str, password: str) -> Tuple[bool, str]:
    """Validate user credential formatting (supports emails or usernames)."""
    user = username.strip().lower()
    if not user:
        return False, "Username or email is required."

    if len(user) < 3 or len(user) > 100:
        return False, "Username/email must be between 3 and 100 characters."

    # Validate email or standard username format
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
