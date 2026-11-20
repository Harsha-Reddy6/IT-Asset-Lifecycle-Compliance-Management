import json
from flask import Blueprint, render_template, session, redirect, url_for
from database import execute_query
from utils.auth import login_required
from services.audit_service import get_recent_logs

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
@login_required
def dashboard_view():
    user_id = session.get("user_id")
    role = session.get("role", "employee")
    
    # 1. Fetch Dynamic System KPI Metrics from MySQL
    metrics_query = """
        SELECT
            (SELECT COUNT(*) FROM assets) AS total_assets,
            (SELECT COUNT(*) FROM assets WHERE asset_status = 'Assigned') AS assigned_assets,
            (SELECT COUNT(*) FROM assets WHERE asset_status = 'Available') AS available_assets,
            (SELECT COUNT(*) FROM assets WHERE asset_status = 'Under Maintenance') AS maintenance_assets,
            (SELECT COUNT(*) FROM employees WHERE employee_status = 'Active') AS total_employees,
            (SELECT COUNT(*) FROM departments) AS total_departments,
            (SELECT COALESCE(SUM(total_licenses), 0) FROM software_licenses) AS total_software_licenses,
            (SELECT COUNT(*) FROM software_licenses WHERE license_status = 'Expired' OR expiry_date < CURDATE()) AS expired_licenses,
            (
                (SELECT COALESCE(SUM(total_licenses), 0) FROM software_licenses WHERE license_status = 'Active') -
                (SELECT COUNT(*) FROM license_assignments WHERE assignment_status = 'Assigned')
            ) AS available_licenses,
            (SELECT COUNT(*) FROM compliance_alerts WHERE alert_status = 'Open') AS open_alerts
    """
    kpis = execute_query(metrics_query, fetch_one=True) or {}
    
    # Ensure non-negative available licenses
    if kpis.get("available_licenses") is not None and kpis["available_licenses"] < 0:
        kpis["available_licenses"] = 0
        
    # 2. Charts Data (Pure MySQL Aggregations)
    
    # Chart 1: Asset Status Distribution
    status_query = """
        SELECT asset_status, COUNT(*) AS count
        FROM assets
        GROUP BY asset_status
    """
    status_rows = execute_query(status_query, fetch_all=True) or []
    chart_asset_status = {
        "labels": [r["asset_status"] for r in status_rows],
        "data": [r["count"] for r in status_rows]
    }
    
    # Chart 2: Assets by Category
    category_query = """
        SELECT COALESCE(c.category_name, 'Uncategorized') AS category_name, COUNT(a.asset_id) AS count
        FROM asset_categories c
        LEFT JOIN assets a ON c.category_id = a.category_id
        GROUP BY c.category_id, c.category_name
        ORDER BY count DESC
    """
    cat_rows = execute_query(category_query, fetch_all=True) or []
    chart_categories = {
        "labels": [r["category_name"] for r in cat_rows],
        "data": [r["count"] for r in cat_rows]
    }
    
    # Chart 3: Monthly Asset Purchases (Last 6-12 months)
    purchases_query = """
        SELECT 
            DATE_FORMAT(purchase_date, '%b %Y') AS month_label,
            DATE_FORMAT(purchase_date, '%Y-%m') AS ym,
            COUNT(*) AS count,
            COALESCE(SUM(purchase_cost), 0) AS total_spend
        FROM assets
        WHERE purchase_date IS NOT NULL
        GROUP BY ym, month_label
        ORDER BY ym ASC
        LIMIT 12
    """
    purchase_rows = execute_query(purchases_query, fetch_all=True) or []
    chart_purchases = {
        "labels": [r["month_label"] for r in purchase_rows],
        "counts": [r["count"] for r in purchase_rows],
        "spend": [float(r["total_spend"]) for r in purchase_rows]
    }
    
    # Chart 4: License Status Distribution
    license_status_query = """
        SELECT license_status, COUNT(*) AS count
        FROM software_licenses
        GROUP BY license_status
    """
    lic_rows = execute_query(license_status_query, fetch_all=True) or []
    chart_licenses = {
        "labels": [r["license_status"] for r in lic_rows],
        "data": [r["count"] for r in lic_rows]
    }
    
    # Chart 5: Compliance Alerts by Type
    compliance_query = """
        SELECT alert_type, COUNT(*) AS count
        FROM compliance_alerts
        WHERE alert_status = 'Open'
        GROUP BY alert_type
    """
    comp_rows = execute_query(compliance_query, fetch_all=True) or []
    chart_compliance = {
        "labels": [r["alert_type"] for r in comp_rows],
        "data": [r["count"] for r in comp_rows]
    }
    
    # 3. Recent Audit Activity
    recent_activities = get_recent_logs(limit=8)
    
    # 4. Expiring Warranties (Within 60 Days or Expired)
    expiring_warranties = execute_query("""
        SELECT asset_id, asset_code, asset_name, warranty_expiry,
               DATEDIFF(warranty_expiry, CURDATE()) AS days_left
        FROM assets
        WHERE warranty_expiry IS NOT NULL 
          AND warranty_expiry <= DATE_ADD(CURDATE(), INTERVAL 60 DAY)
        ORDER BY warranty_expiry ASC
        LIMIT 5
    """, fetch_all=True)
    
    # 5. Expiring Licenses (Within 60 Days or Expired)
    expiring_licenses = execute_query("""
        SELECT sl.license_id, s.software_name, sl.license_key, sl.expiry_date,
               DATEDIFF(sl.expiry_date, CURDATE()) AS days_left
        FROM software_licenses sl
        JOIN software s ON sl.software_id = s.software_id
        WHERE sl.expiry_date IS NOT NULL
          AND sl.expiry_date <= DATE_ADD(CURDATE(), INTERVAL 60 DAY)
        ORDER BY sl.expiry_date ASC
        LIMIT 5
    """, fetch_all=True)
    
    # 6. Employee specific assignments if employee role
    emp_assignments = []
    emp_licenses = []
    if role == "employee":
        emp = execute_query("SELECT employee_id FROM employees WHERE user_id = %s", (user_id,), fetch_one=True)
        if emp:
            emp_id = emp["employee_id"]
            emp_assignments = execute_query("""
                SELECT aa.*, a.asset_code, a.asset_name, a.location, c.category_name
                FROM asset_assignments aa
                JOIN assets a ON aa.asset_id = a.asset_id
                LEFT JOIN asset_categories c ON a.category_id = c.category_id
                WHERE aa.employee_id = %s AND aa.assignment_status = 'Assigned'
            """, (emp_id,), fetch_all=True)
            
            emp_licenses = execute_query("""
                SELECT la.*, s.software_name, s.publisher, s.version, sl.expiry_date
                FROM license_assignments la
                JOIN software_licenses sl ON la.license_id = sl.license_id
                JOIN software s ON sl.software_id = s.software_id
                WHERE la.employee_id = %s AND la.assignment_status = 'Assigned'
            """, (emp_id,), fetch_all=True)

    return render_template(
        "dashboard.html",
        kpis=kpis,
        chart_asset_status=chart_asset_status,
        chart_categories=chart_categories,
        chart_purchases=chart_purchases,
        chart_licenses=chart_licenses,
        chart_compliance=chart_compliance,
        recent_activities=recent_activities,
        expiring_warranties=expiring_warranties,
        expiring_licenses=expiring_licenses,
        emp_assignments=emp_assignments,
        emp_licenses=emp_licenses,
        role=role
    )
