import csv
import io
from flask import Blueprint, render_template, request, Response, session, redirect, url_for, flash
from database import execute_query
from utils.auth import login_required

report_bp = Blueprint("reports", __name__)

@report_bp.route("/reports")
@login_required
def reports_hub():
    # High level report summaries
    asset_summary = execute_query("""
        SELECT 
            COUNT(*) AS total_assets,
            COALESCE(SUM(purchase_cost), 0) AS total_valuation,
            COUNT(CASE WHEN asset_status = 'Assigned' THEN 1 END) AS assigned_count,
            COUNT(CASE WHEN asset_status = 'Available' THEN 1 END) AS available_count,
            COUNT(CASE WHEN asset_status = 'Under Maintenance' THEN 1 END) AS maintenance_count
        FROM assets
    """, fetch_one=True)
    
    license_summary = execute_query("""
        SELECT 
            COUNT(*) AS total_licenses,
            COALESCE(SUM(total_licenses), 0) AS total_seats,
            COALESCE(SUM(license_cost), 0) AS total_spend,
            COUNT(CASE WHEN license_status = 'Expired' OR expiry_date < CURDATE() THEN 1 END) AS expired_licenses
        FROM software_licenses
    """, fetch_one=True)
    
    compliance_summary = execute_query("""
        SELECT 
            COUNT(CASE WHEN alert_status = 'Open' THEN 1 END) AS open_alerts,
            COUNT(CASE WHEN alert_status = 'Resolved' THEN 1 END) AS resolved_alerts
        FROM compliance_alerts
    """, fetch_one=True)
    
    return render_template(
        "reports.html",
        active_tab="hub",
        asset_summary=asset_summary,
        license_summary=license_summary,
        compliance_summary=compliance_summary
    )

@report_bp.route("/reports/assets")
@login_required
def report_assets():
    status = request.args.get("status", "")
    category_id = request.args.get("category_id", "")
    
    where_clauses = ["1=1"]
    params = []
    if status:
        where_clauses.append("a.asset_status = %s")
        params.append(status)
    if category_id:
        where_clauses.append("a.category_id = %s")
        params.append(category_id)
        
    where_sql = " AND ".join(where_clauses)
    
    assets = execute_query(f"""
        SELECT 
            a.*,
            c.category_name,
            v.vendor_name,
            e.full_name AS assigned_to_name,
            e.employee_code AS assigned_to_code
        FROM assets a
        LEFT JOIN asset_categories c ON a.category_id = c.category_id
        LEFT JOIN vendors v ON a.vendor_id = v.vendor_id
        LEFT JOIN asset_assignments aa ON a.asset_id = aa.asset_id AND aa.assignment_status = 'Assigned'
        LEFT JOIN employees e ON aa.employee_id = e.employee_id
        WHERE {where_sql}
        ORDER BY a.asset_id DESC
    """, tuple(params), fetch_all=True)
    
    categories = execute_query("SELECT category_id, category_name FROM asset_categories ORDER BY category_name", fetch_all=True)
    
    return render_template(
        "reports.html",
        active_tab="assets",
        assets=assets,
        categories=categories,
        selected_status=status,
        selected_category=category_id
    )

@report_bp.route("/reports/licenses")
@login_required
def report_licenses():
    licenses = execute_query("""
        SELECT 
            sl.license_id,
            s.software_name,
            s.publisher,
            s.version,
            sl.license_key,
            sl.total_licenses,
            sl.purchase_date,
            sl.expiry_date,
            sl.license_cost,
            sl.license_status,
            v.vendor_name,
            COUNT(CASE WHEN la.assignment_status = 'Assigned' THEN 1 END) AS assigned_count,
            (sl.total_licenses - COUNT(CASE WHEN la.assignment_status = 'Assigned' THEN 1 END)) AS available_count
        FROM software_licenses sl
        JOIN software s ON sl.software_id = s.software_id
        LEFT JOIN vendors v ON sl.vendor_id = v.vendor_id
        LEFT JOIN license_assignments la ON sl.license_id = la.license_id
        GROUP BY sl.license_id, s.software_name, s.publisher, s.version, sl.license_key, 
                 sl.total_licenses, sl.purchase_date, sl.expiry_date, sl.license_cost, 
                 sl.license_status, v.vendor_name
        ORDER BY sl.license_id DESC
    """, fetch_all=True)
    
    return render_template(
        "reports.html",
        active_tab="licenses",
        licenses=licenses
    )

@report_bp.route("/reports/compliance")
@login_required
def report_compliance():
    alerts = execute_query("""
        SELECT 
            ca.*,
            a.asset_code,
            a.asset_name,
            s.software_name
        FROM compliance_alerts ca
        LEFT JOIN assets a ON ca.asset_id = a.asset_id
        LEFT JOIN software_licenses sl ON ca.license_id = sl.license_id
        LEFT JOIN software s ON sl.software_id = s.software_id
        ORDER BY ca.alert_id DESC
    """, fetch_all=True)
    
    audit_logs = execute_query("""
        SELECT al.*, u.username, u.full_name AS user_name
        FROM audit_logs al
        LEFT JOIN users u ON al.user_id = u.id
        ORDER BY al.log_id DESC
        LIMIT 50
    """, fetch_all=True)
    
    return render_template(
        "reports.html",
        active_tab="compliance",
        alerts=alerts,
        audit_logs=audit_logs
    )

@report_bp.route("/reports/export")
@login_required
def export_csv():
    report_type = request.args.get("type", "assets")
    output = io.StringIO()
    writer = csv.writer(output)
    
    if report_type == "assets":
        writer.writerow(["Asset Code", "Asset Name", "Category", "Brand", "Model", "Serial Number", "Purchase Date", "Cost", "Warranty Expiry", "Location", "Status"])
        rows = execute_query("""
            SELECT a.asset_code, a.asset_name, c.category_name, a.brand, a.model_number,
                   a.serial_number, a.purchase_date, a.purchase_cost, a.warranty_expiry, a.location, a.asset_status
            FROM assets a
            LEFT JOIN asset_categories c ON a.category_id = c.category_id
            ORDER BY a.asset_id ASC
        """, fetch_all=True)
        for r in rows:
            writer.writerow([
                r["asset_code"], r["asset_name"], r["category_name"] or "N/A", r["brand"] or "N/A",
                r["model_number"] or "N/A", r["serial_number"] or "N/A", r["purchase_date"] or "N/A",
                r["purchase_cost"] or 0, r["warranty_expiry"] or "N/A", r["location"] or "N/A", r["asset_status"]
            ])
        filename = "it_assets_inventory.csv"
        
    elif report_type == "licenses":
        writer.writerow(["Software Name", "Publisher", "Version", "License Key", "Total Seats", "Assigned Seats", "Available Seats", "Expiry Date", "Cost", "Status"])
        rows = execute_query("""
            SELECT s.software_name, s.publisher, s.version, sl.license_key, sl.total_licenses,
                   COUNT(CASE WHEN la.assignment_status = 'Assigned' THEN 1 END) AS assigned_count,
                   (sl.total_licenses - COUNT(CASE WHEN la.assignment_status = 'Assigned' THEN 1 END)) AS available_count,
                   sl.expiry_date, sl.license_cost, sl.license_status
            FROM software_licenses sl
            JOIN software s ON sl.software_id = s.software_id
            LEFT JOIN license_assignments la ON sl.license_id = la.license_id
            GROUP BY sl.license_id, s.software_name, s.publisher, s.version, sl.license_key,
                     sl.total_licenses, sl.expiry_date, sl.license_cost, sl.license_status
        """, fetch_all=True)
        for r in rows:
            writer.writerow([
                r["software_name"], r["publisher"] or "N/A", r["version"] or "N/A", r["license_key"] or "N/A",
                r["total_licenses"], r["assigned_count"], r["available_count"], r["expiry_date"] or "N/A",
                r["license_cost"] or 0, r["license_status"]
            ])
        filename = "software_licenses_compliance.csv"
        
    elif report_type == "assignments":
        writer.writerow(["Asset Code", "Asset Name", "Employee Code", "Employee Name", "Department", "Assigned Date", "Return Date", "Status", "Remarks"])
        rows = execute_query("""
            SELECT a.asset_code, a.asset_name, e.employee_code, e.full_name, d.department_name,
                   aa.assigned_date, aa.return_date, aa.assignment_status, aa.remarks
            FROM asset_assignments aa
            JOIN assets a ON aa.asset_id = a.asset_id
            JOIN employees e ON aa.employee_id = e.employee_id
            LEFT JOIN departments d ON e.department_id = d.department_id
            ORDER BY aa.assignment_id DESC
        """, fetch_all=True)
        for r in rows:
            writer.writerow([
                r["asset_code"], r["asset_name"], r["employee_code"], r["full_name"], r["department_name"] or "N/A",
                r["assigned_date"], r["return_date"] or "N/A", r["assignment_status"], r["remarks"] or ""
            ])
        filename = "asset_assignments.csv"
        
    else:  # compliance alerts
        writer.writerow(["Alert ID", "Type", "Status", "Message", "Created Date"])
        rows = execute_query("SELECT alert_id, alert_type, alert_status, alert_message, alert_date FROM compliance_alerts ORDER BY alert_id DESC", fetch_all=True)
        for r in rows:
            writer.writerow([r["alert_id"], r["alert_type"], r["alert_status"], r["alert_message"], r["alert_date"]])
        filename = "compliance_alerts.csv"
        
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
