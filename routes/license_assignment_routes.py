from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import execute_query
from utils.auth import login_required, admin_required
from services.license_service import get_license_assignments, assign_license, return_license

license_assignment_bp = Blueprint("license_assignments", __name__)

@license_assignment_bp.route("/license-assignments")
@login_required
def license_assignments_list():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    page = request.args.get("page", 1, type=int)
    
    assignments, pagination = get_license_assignments(search=search, status=status, page=page, per_page=10)
    
    # Active licenses with available seats
    active_licenses = execute_query("""
        SELECT 
            sl.license_id,
            s.software_name,
            s.version,
            sl.total_licenses,
            (sl.total_licenses - COUNT(CASE WHEN la.assignment_status = 'Assigned' THEN 1 END)) AS available_seats
        FROM software_licenses sl
        JOIN software s ON sl.software_id = s.software_id
        LEFT JOIN license_assignments la ON sl.license_id = la.license_id
        WHERE sl.license_status = 'Active' AND (sl.expiry_date IS NULL OR sl.expiry_date >= CURDATE())
        GROUP BY sl.license_id, s.software_name, s.version, sl.total_licenses
        HAVING available_seats > 0
        ORDER BY s.software_name
    """, fetch_all=True)
    
    active_employees = execute_query(
        "SELECT employee_id, employee_code, full_name, email FROM employees WHERE employee_status = 'Active' ORDER BY full_name",
        fetch_all=True
    )
    
    return render_template(
        "license_assignments.html",
        assignments=assignments,
        pagination=pagination,
        search=search,
        selected_status=status,
        active_licenses=active_licenses,
        active_employees=active_employees
    )

@license_assignment_bp.route("/license-assignments/add", methods=["GET", "POST"])
@admin_required
def add_license_assignment():
    active_licenses = execute_query("""
        SELECT 
            sl.license_id,
            s.software_name,
            s.version,
            sl.total_licenses,
            (sl.total_licenses - COUNT(CASE WHEN la.assignment_status = 'Assigned' THEN 1 END)) AS available_seats
        FROM software_licenses sl
        JOIN software s ON sl.software_id = s.software_id
        LEFT JOIN license_assignments la ON sl.license_id = la.license_id
        WHERE sl.license_status = 'Active' AND (sl.expiry_date IS NULL OR sl.expiry_date >= CURDATE())
        GROUP BY sl.license_id, s.software_name, s.version, sl.total_licenses
        HAVING available_seats > 0
        ORDER BY s.software_name
    """, fetch_all=True)
    
    active_employees = execute_query(
        "SELECT employee_id, employee_code, full_name, email FROM employees WHERE employee_status = 'Active' ORDER BY full_name",
        fetch_all=True
    )
    
    if request.method == "POST":
        license_id = request.form.get("license_id", type=int)
        employee_id = request.form.get("employee_id", type=int)
        
        if not license_id:
            flash("Please select a software license.", "danger")
            return render_template("license_assignments.html", action="add", active_licenses=active_licenses, active_employees=active_employees)
            
        if not employee_id:
            flash("Please select an employee.", "danger")
            return render_template("license_assignments.html", action="add", active_licenses=active_licenses, active_employees=active_employees)
            
        try:
            assign_license(license_id, employee_id, session.get("user_id"))
            flash("Software license seat allocated successfully.", "success")
            return redirect(url_for("license_assignments.license_assignments_list"))
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("license_assignments.html", action="add", active_licenses=active_licenses, active_employees=active_employees, form=request.form)
            
    return render_template("license_assignments.html", action="add", active_licenses=active_licenses, active_employees=active_employees)

@license_assignment_bp.route("/license-assignments/return/<int:id>", methods=["POST"])
@admin_required
def return_license_assignment(id):
    try:
        return_license(id, session.get("user_id"))
        flash("Software license seat returned and available for reallocation.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("license_assignments.license_assignments_list"))
