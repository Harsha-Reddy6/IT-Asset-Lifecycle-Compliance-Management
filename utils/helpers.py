import math
from datetime import date, datetime
from decimal import Decimal

def paginate(total_items: int, page: int = 1, per_page: int = 10) -> dict:
    """Computes pagination metadata."""
    page = max(1, int(page or 1))
    per_page = max(1, int(per_page or 10))
    total_pages = max(1, math.ceil(total_items / per_page))
    if page > total_pages:
        page = total_pages
    offset = (page - 1) * per_page
    
    return {
        "page": page,
        "per_page": per_page,
        "total_items": total_items,
        "total_pages": total_pages,
        "offset": offset,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "prev_page": page - 1,
        "next_page": page + 1,
    }

def format_currency(amount) -> str:
    """Formats numeric or decimal value as standard currency ($XX,XXX.XX)."""
    if amount is None or amount == "":
        return "$0.00"
    try:
        val = float(amount)
        return f"${val:,.2f}"
    except (ValueError, TypeError):
        return "$0.00"

def format_date(dt, fmt: str = "%b %d, %Y") -> str:
    """Formats date or datetime object for clean UI display."""
    if not dt:
        return "N/A"
    if isinstance(dt, (date, datetime)):
        return dt.strftime(fmt)
    try:
        parsed = datetime.strptime(str(dt).split()[0], "%Y-%m-%d")
        return parsed.strftime(fmt)
    except Exception:
        return str(dt)

def is_expired(date_val) -> bool:
    """Checks if a date is in the past."""
    if not date_val:
        return False
    if isinstance(date_val, datetime):
        date_val = date_val.date()
    elif isinstance(date_val, str):
        try:
            date_val = datetime.strptime(date_val.split()[0], "%Y-%m-%d").date()
        except Exception:
            return False
    return date_val < date.today()

def days_until(date_val) -> int | None:
    """Returns number of days until target date, or negative if passed."""
    if not date_val:
        return None
    if isinstance(date_val, datetime):
        date_val = date_val.date()
    elif isinstance(date_val, str):
        try:
            date_val = datetime.strptime(date_val.split()[0], "%Y-%m-%d").date()
        except Exception:
            return None
    return (date_val - date.today()).days
