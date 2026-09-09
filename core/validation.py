"""
validation.py — Parameter & Credential Validation Logic.
"""

import re
from typing import Dict, Tuple
from core.helpers import FEATURE_COLS, VALIDATION_RANGES

# Strict Gmail email format regex
GMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@gmail\.com$"


def validate_gmail(email: str) -> Tuple[bool, str]:
    """Validate that the input email address is a valid @gmail.com address."""
    clean_email = email.strip().lower()
    if not clean_email:
        return False, "Gmail address is required."
    
    if not re.match(GMAIL_REGEX, clean_email):
        return False, "Invalid email format. Only valid Gmail addresses (@gmail.com) are accepted."
        
    return True, ""


def validate_credentials(email: str, password: str) -> Tuple[bool, str]:
    """Validate Gmail formatting and password security rules."""
    is_valid_email, msg = validate_gmail(email)
    if not is_valid_email:
        return False, msg

    if not password or len(password) < 4:
        return False, "Password must be at least 4 characters long."

    return True, ""


def parse_form_features(form_data: Dict[str, str]) -> Dict[str, float]:
    """Parse HTTP request form fields into float feature values with safe default fallback."""
    form_values = {}
    for col in FEATURE_COLS:
        val_str = form_data.get(col, "")
        try:
            val = float(val_str)
            # Bound validation check
            vmin = VALIDATION_RANGES[col]["min"]
            vmax = VALIDATION_RANGES[col]["max"]
            form_values[col] = max(vmin, min(vmax, val))
        except (ValueError, TypeError):
            form_values[col] = VALIDATION_RANGES[col]["default"]
    return form_values
