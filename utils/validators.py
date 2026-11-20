import re
from datetime import datetime

EMAIL_REGEX = re.compile(r"^[\w\.-]+@([\w-]+\.)+[\w-]{2,4}$")
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_.-]{3,50}$")

def validate_non_empty(val: str, field_name: str = "Field") -> tuple[bool, str]:
    if val is None or not str(val).strip():
        return False, f"{field_name} is required."
    return True, ""

def validate_email(email: str) -> tuple[bool, str]:
    if not email or not EMAIL_REGEX.match(email.strip()):
        return False, "Please provide a valid email address."
    return True, ""

def validate_username(username: str) -> tuple[bool, str]:
    if not username or not USERNAME_REGEX.match(username.strip()):
        return False, "Username must be 3-50 alphanumeric characters (letters, numbers, underscore, dot, hyphen)."
    return True, ""

def validate_password_strength(password: str) -> tuple[bool, str]:
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long."
    return True, ""

def validate_positive_number(val, field_name: str = "Amount", allow_zero: bool = True) -> tuple[bool, str, float]:
    try:
        num = float(val)
        if allow_zero and num < 0:
            return False, f"{field_name} cannot be negative.", 0.0
        if not allow_zero and num <= 0:
            return False, f"{field_name} must be greater than zero.", 0.0
        return True, "", num
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid numeric value.", 0.0

def validate_positive_int(val, field_name: str = "Quantity", allow_zero: bool = False) -> tuple[bool, str, int]:
    try:
        num = int(val)
        if allow_zero and num < 0:
            return False, f"{field_name} cannot be negative.", 0
        if not allow_zero and num <= 0:
            return False, f"{field_name} must be greater than zero.", 0
        return True, "", num
    except (ValueError, TypeError):
        return False, f"{field_name} must be an integer.", 0

def validate_date(date_str: str, field_name: str = "Date", required: bool = False) -> tuple[bool, str, str | None]:
    if not date_str or not str(date_str).strip():
        if required:
            return False, f"{field_name} is required.", None
        return True, "", None
    try:
        # Check standard format YYYY-MM-DD
        dt = datetime.strptime(str(date_str).strip(), "%Y-%m-%d")
        return True, "", dt.strftime("%Y-%m-%d")
    except ValueError:
        return False, f"{field_name} must be in YYYY-MM-DD format.", None

def validate_choice(val: str, allowed_choices: list | tuple | set, field_name: str = "Status") -> tuple[bool, str]:
    if val not in allowed_choices:
        return False, f"{field_name} must be one of: {', '.join(map(str, allowed_choices))}."
    return True, ""
