from database import execute_query

def log_audit(user_id: int | None, action: str, description: str):
    """
    Records an entry in the audit_logs table.
    Ensures full compliance and traceability across system actions.
    """
    sql = """
        INSERT INTO audit_logs (user_id, action, description, created_at)
        VALUES (%s, %s, %s, NOW())
    """
    try:
        execute_query(sql, (user_id, action, description), commit=True)
    except Exception as e:
        print(f"[Audit Log Error] Failed to record log: {e}")

def get_recent_logs(limit: int = 10):
    """Retrieves the most recent audit logs with user information."""
    sql = """
        SELECT 
            al.log_id,
            al.user_id,
            al.action,
            al.description,
            al.created_at,
            u.username,
            u.full_name AS user_name,
            u.role AS user_role
        FROM audit_logs al
        LEFT JOIN users u ON al.user_id = u.id
        ORDER BY al.log_id DESC
        LIMIT %s
    """
    return execute_query(sql, (limit,), fetch_all=True)
