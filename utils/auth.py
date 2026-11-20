import secrets
from functools import wraps
from flask import session, redirect, url_for, flash, request, abort
import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password: str) -> str:
    """Hashes a password securely using bcrypt."""
    if not password:
        raise ValueError("Password cannot be empty")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against a hash.
    Compatible with both bcrypt ($2a$, $2b$, $2y$) and Werkzeug hashes (scrypt, pbkdf2).
    """
    if not plain_password or not hashed_password:
        return False
    try:
        # Check if bcrypt hash
        if hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        # Fallback to Werkzeug security
        return check_password_hash(hashed_password, plain_password)
    except Exception as e:
        print(f"[Password Verification Error] {e}")
        return False

def generate_csrf_token() -> str:
    """Generates and stores a CSRF token in the user's session."""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]

def validate_csrf_token(token: str) -> bool:
    """Validates submitted CSRF token against session."""
    session_token = session.get("_csrf_token")
    if not session_token or not token:
        return False
    return secrets.compare_digest(session_token, token)

def login_required(f):
    """Decorator ensuring that only authenticated users can access the endpoint."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator ensuring that only Admin users can access the endpoint."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        if session.get("role") != "admin":
            flash("Access denied: Administrator privileges are required for this action.", "danger")
            return redirect(url_for("dashboard.dashboard_view"))
        return f(*args, **kwargs)
    return decorated_function
