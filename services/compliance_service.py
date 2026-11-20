from database import execute_query, get_db_cursor
from services.audit_service import log_audit
from utils.helpers import paginate

def run_compliance_scan(user_id: int = None) -> int:
    """
    Automated scan that analyzes asset warranties and software license lifecycles.
    Detects expired items and items expiring within 30 days, generating open compliance alerts.
    Prevents duplicate unresolved alerts.
    """
    new_alerts_count = 0
    
    with get_db_cursor(commit=True) as (cursor, _):
        # 1. Expired Software Licenses
        cursor.execute("""
            SELECT sl.license_id, s.software_name, sl.expiry_date
            FROM software_licenses sl
            JOIN software s ON sl.software_id = s.software_id
            WHERE sl.expiry_date IS NOT NULL 
              AND sl.expiry_date < CURDATE() 
              AND sl.license_status != 'Cancelled'
        """)
        expired_licenses = cursor.fetchall()
        for lic in expired_licenses:
            cursor.execute("""
                SELECT alert_id FROM compliance_alerts
                WHERE license_id = %s AND alert_type = 'License Expired' AND alert_status = 'Open'
            """, (lic["license_id"],))
            if not cursor.fetchone():
                msg = f"Software license for '{lic['software_name']}' expired on {lic['expiry_date']}."
                cursor.execute("""
                    INSERT INTO compliance_alerts (license_id, alert_type, alert_message, alert_status, alert_date)
                    VALUES (%s, 'License Expired', %s, 'Open', NOW())
                """, (lic["license_id"], msg))
                new_alerts_count += 1
                
        # 2. Licenses Expiring within 30 Days
        cursor.execute("""
            SELECT sl.license_id, s.software_name, sl.expiry_date, DATEDIFF(sl.expiry_date, CURDATE()) AS days_left
            FROM software_licenses sl
            JOIN software s ON sl.software_id = s.software_id
            WHERE sl.expiry_date IS NOT NULL 
              AND sl.expiry_date >= CURDATE()
              AND sl.expiry_date <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
              AND sl.license_status = 'Active'
        """)
        expiring_licenses = cursor.fetchall()
        for lic in expiring_licenses:
            cursor.execute("""
                SELECT alert_id FROM compliance_alerts
                WHERE license_id = %s AND alert_type = 'License Expiring Soon' AND alert_status = 'Open'
            """, (lic["license_id"],))
            if not cursor.fetchone():
                msg = f"Software license for '{lic['software_name']}' will expire in {lic['days_left']} day(s) on {lic['expiry_date']}."
                cursor.execute("""
                    INSERT INTO compliance_alerts (license_id, alert_type, alert_message, alert_status, alert_date)
                    VALUES (%s, 'License Expiring Soon', %s, 'Open', NOW())
                """, (lic["license_id"], msg))
                new_alerts_count += 1

        # 3. Expired Asset Warranties
        cursor.execute("""
            SELECT a.asset_id, a.asset_name, a.asset_code, a.warranty_expiry
            FROM assets a
            WHERE a.warranty_expiry IS NOT NULL 
              AND a.warranty_expiry < CURDATE()
              AND a.asset_status != 'Retired'
        """)
        expired_warranties = cursor.fetchall()
        for ast in expired_warranties:
            cursor.execute("""
                SELECT alert_id FROM compliance_alerts
                WHERE asset_id = %s AND alert_type = 'Warranty Expired' AND alert_status = 'Open'
            """, (ast["asset_id"],))
            if not cursor.fetchone():
                msg = f"Warranty for hardware asset '{ast['asset_name']}' ({ast['asset_code']}) expired on {ast['warranty_expiry']}."
                cursor.execute("""
                    INSERT INTO compliance_alerts (asset_id, alert_type, alert_message, alert_status, alert_date)
                    VALUES (%s, 'Warranty Expired', %s, 'Open', NOW())
                """, (ast["asset_id"], msg))
                new_alerts_count += 1

        # 4. Asset Warranties Expiring within 30 Days
        cursor.execute("""
            SELECT a.asset_id, a.asset_name, a.asset_code, a.warranty_expiry, DATEDIFF(a.warranty_expiry, CURDATE()) AS days_left
            FROM assets a
            WHERE a.warranty_expiry IS NOT NULL 
              AND a.warranty_expiry >= CURDATE()
              AND a.warranty_expiry <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
              AND a.asset_status != 'Retired'
        """)
        expiring_warranties = cursor.fetchall()
        for ast in expiring_warranties:
            cursor.execute("""
                SELECT alert_id FROM compliance_alerts
                WHERE asset_id = %s AND alert_type = 'Warranty Expiring Soon' AND alert_status = 'Open'
            """, (ast["asset_id"],))
            if not cursor.fetchone():
                msg = f"Warranty for hardware asset '{ast['asset_name']}' ({ast['asset_code']}) expires in {ast['days_left']} day(s) on {ast['warranty_expiry']}."
                cursor.execute("""
                    INSERT INTO compliance_alerts (asset_id, alert_type, alert_message, alert_status, alert_date)
                    VALUES (%s, 'Warranty Expiring Soon', %s, 'Open', NOW())
                """, (ast["asset_id"], msg))
                new_alerts_count += 1
                
    if user_id:
        log_audit(user_id, "COMPLIANCE_RUN", f"Executed compliance audit. {new_alerts_count} new alerts generated.")
        
    return new_alerts_count

def get_alerts(status: str = "Open", alert_type: str = None, page: int = 1, per_page: int = 10):
    """Retrieves paginated compliance alerts."""
    where_clauses = ["1=1"]
    params = []
    
    if status and status != "All":
        where_clauses.append("ca.alert_status = %s")
        params.append(status)
        
    if alert_type and alert_type != "All":
        where_clauses.append("ca.alert_type = %s")
        params.append(alert_type)
        
    where_sql = " AND ".join(where_clauses)
    
    count_sql = f"SELECT COUNT(*) AS total FROM compliance_alerts ca WHERE {where_sql}"
    count_row = execute_query(count_sql, tuple(params), fetch_one=True)
    total_items = count_row["total"] if count_row else 0
    
    pagination = paginate(total_items, page, per_page)
    
    data_sql = f"""
        SELECT 
            ca.alert_id,
            ca.asset_id,
            ca.license_id,
            ca.alert_type,
            ca.alert_message,
            ca.alert_date,
            ca.alert_status,
            a.asset_code,
            a.asset_name,
            s.software_name,
            sl.license_key
        FROM compliance_alerts ca
        LEFT JOIN assets a ON ca.asset_id = a.asset_id
        LEFT JOIN software_licenses sl ON ca.license_id = sl.license_id
        LEFT JOIN software s ON sl.software_id = s.software_id
        WHERE {where_sql}
        ORDER BY ca.alert_id DESC
        LIMIT %s OFFSET %s
    """
    data_params = list(params) + [pagination["per_page"], pagination["offset"]]
    items = execute_query(data_sql, tuple(data_params), fetch_all=True)
    return items, pagination

def resolve_alert(alert_id: int, user_id: int):
    """Marks a compliance alert as Resolved."""
    alert = execute_query("SELECT * FROM compliance_alerts WHERE alert_id = %s", (alert_id,), fetch_one=True)
    if not alert:
        raise ValueError("Compliance alert not found.")
    if alert["alert_status"] == "Resolved":
        raise ValueError("Alert is already resolved.")
        
    sql = "UPDATE compliance_alerts SET alert_status = 'Resolved' WHERE alert_id = %s"
    execute_query(sql, (alert_id,), commit=True)
    log_audit(user_id, "COMPLIANCE_RESOLVE", f"Resolved {alert['alert_type']} alert (ID: {alert_id})")

def get_compliance_stats() -> dict:
    """Returns aggregated compliance metrics."""
    sql = """
        SELECT
            COUNT(CASE WHEN alert_status = 'Open' THEN 1 END) AS open_alerts,
            COUNT(CASE WHEN alert_status = 'Open' AND alert_type LIKE '%Expired%' THEN 1 END) AS expired_count,
            COUNT(CASE WHEN alert_status = 'Open' AND alert_type LIKE '%Expiring Soon%' THEN 1 END) AS expiring_soon_count,
            COUNT(CASE WHEN alert_status = 'Resolved' THEN 1 END) AS resolved_alerts
        FROM compliance_alerts
    """
    stats = execute_query(sql, fetch_one=True)
    return stats or {
        "open_alerts": 0,
        "expired_count": 0,
        "expiring_soon_count": 0,
        "resolved_alerts": 0
    }
