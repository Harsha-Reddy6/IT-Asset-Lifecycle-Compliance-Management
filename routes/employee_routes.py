from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import execute_query, get_db_cursor
from utils.auth import login_required, admin_required
from utils.validators import validate_email, validate_non_empty, validate_choice
from utils.helpers import paginate
from services.audit_service import log_audit

employee_bp = Blueprint("employees", __name__)

@employee_bp.route("/employees")
@login_required
def employees_list():
    search = request.args.get("search", "").strip()
    dept_id = request.args.get("dept_id", "").strip()
    status = request.args.get("status", "").strip()
    page = request.args.get("page", 1, type=int)
    
    where_clauses = ["1=1"]
    params = []
    
    if search:
        s_term = f"%{search}%"
        where_clauses.append("(e.full_name LIKE %s OR e.employee_code LIKE %s OR e.email LIKE %s OR e.designation LIKE %s)")
        params.extend([s_term, s_term, s_term, s_term])
        
    if dept_id:
        where_clauses.append("e.department_id = %s")
        params.append(dept_id)
        
    if status:
        where_clauses.append("e.employee_status = %s")
        params.append(status)
        
    where_sql = " AND ".join(where_clauses)
    
    # Total count
    count_sql = f"SELECT COUNT(*) AS total FROM employees e WHERE {where_sql}"
    count_row = execute_query(count_sql, tuple(params), fetch_one=True)
    total_items = count_row["total"] if count_row else 0
    
    pagination = paginate(total_items, page, 10)
    
    # Query employees with department name and active assigned counts
    data_sql = f"""
        SELECT 
            e.*,
            d.department_name,
            u.username,
            (SELECT COUNT(*) FROM asset_assignments aa WHERE aa.employee_id = e.employee_id AND aa.assignment_status = 'Assigned') AS assigned_assets_count,
            (SELECT COUNT(*) FROM license_assignments la WHERE la.employee_id = e.employee_id AND la.assignment_status = 'Assigned') AS assigned_licenses_count
        FROM employees e
        LEFT JOIN departments d ON e.department_id = d.department_id
        LEFT JOIN users u ON e.user_id = u.id
        WHERE {where_sql}
        ORDER BY e.employee_id DESC
        LIMIT %s OFFSET %s
    """
    data_params = list(params) + [pagination["per_page"], pagination["offset"]]
    employees = execute_query(data_sql, tuple(data_params), fetch_all=True)
    
    # Dropdowns
    departments = execute_query("SELECT department_id, department_name FROM departments ORDER BY department_name", fetch_all=True)
    
    return render_template(
        "employees.html",
        employees=employees,
        departments=departments,
        pagination=pagination,
        search=search,
        selected_dept=dept_id,
        selected_status=status
    )

@employee_bp.route("/employees/add", methods=["GET", "POST"])
@admin_required
def add_employee():
    departments = execute_query("SELECT department_id, department_name FROM departments ORDER BY department_name", fetch_all=True)
    unlinked_users = execute_query("""
        SELECT id, username, full_name, email 
        FROM users 
        WHERE id NOT IN (SELECT user_id FROM employees WHERE user_id IS NOT NULL)
        ORDER BY username
    """, fetch_all=True)
    
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        employee_code = request.form.get("employee_code", "").strip()
        department_id = request.form.get("department_id") or None
        designation = request.form.get("designation", "").strip() or None
        joining_date = request.form.get("joining_date") or None
        employee_status = request.form.get("employee_status", "Active")
        user_id = request.form.get("user_id") or None
        
        valid, err = validate_non_empty(full_name, "Full Name")
        if not valid:
            flash(err, "danger")
            return render_template("employees.html", action="add", departments=departments, unlinked_users=unlinked_users, form=request.form)
            
        valid, err = validate_email(email)
        if not valid:
            flash(err, "danger")
            return render_template("employees.html", action="add", departments=departments, unlinked_users=unlinked_users, form=request.form)
            
        valid, err = validate_non_empty(employee_code, "Employee Code")
        if not valid:
            flash(err, "danger")
            return render_template("employees.html", action="add", departments=departments, unlinked_users=unlinked_users, form=request.form)

        # Check duplicate code or email
        existing = execute_query(
            "SELECT employee_id FROM employees WHERE employee_code = %s OR email = %s",
            (employee_code, email),
            fetch_one=True
        )
        if existing:
            flash("Employee Code or Email is already registered to another employee.", "danger")
            return render_template("employees.html", action="add", departments=departments, unlinked_users=unlinked_users, form=request.form)

        sql = """
            INSERT INTO employees (
                user_id, employee_code, full_name, email,
                department_id, designation, joining_date, employee_status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (user_id, employee_code, full_name, email, department_id, designation, joining_date, employee_status)
        new_id = execute_query(sql, params, commit=True, return_id=True)
        
        log_audit(session.get("user_id"), "EMPLOYEE_CREATE", f"Created employee {full_name} ({employee_code}) with ID {new_id}")
        flash(f"Employee '{full_name}' added successfully.", "success")
        return redirect(url_for("employees.employees_list"))
        
    return render_template("employees.html", action="add", departments=departments, unlinked_users=unlinked_users)

@employee_bp.route("/employees/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_employee(id):
    employee = execute_query("SELECT * FROM employees WHERE employee_id = %s", (id,), fetch_one=True)
    if not employee:
        flash("Employee not found.", "danger")
        return redirect(url_for("employees.employees_list"))
        
    departments = execute_query("SELECT department_id, department_name FROM departments ORDER BY department_name", fetch_all=True)
    unlinked_users = execute_query("""
        SELECT id, username, full_name, email 
        FROM users 
        WHERE id = %s OR id NOT IN (SELECT user_id FROM employees WHERE user_id IS NOT NULL)
        ORDER BY username
    """, (employee.get("user_id") or 0,), fetch_all=True)
    
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        department_id = request.form.get("department_id") or None
        designation = request.form.get("designation", "").strip() or None
        joining_date = request.form.get("joining_date") or None
        employee_status = request.form.get("employee_status", "Active")
        user_id = request.form.get("user_id") or None
        
        valid, err = validate_non_empty(full_name, "Full Name")
        if not valid:
            flash(err, "danger")
            return render_template("employees.html", action="edit", employee=employee, departments=departments, unlinked_users=unlinked_users)
            
        valid, err = validate_email(email)
        if not valid:
            flash(err, "danger")
            return render_template("employees.html", action="edit", employee=employee, departments=departments, unlinked_users=unlinked_users)
            
        # Check duplicate email with another employee
        existing_email = execute_query(
            "SELECT employee_id FROM employees WHERE email = %s AND employee_id != %s",
            (email, id),
            fetch_one=True
        )
        if existing_email:
            flash("Email address is already in use by another employee.", "danger")
            return render_template("employees.html", action="edit", employee=employee, departments=departments, unlinked_users=unlinked_users)

        sql = """
            UPDATE employees SET
                full_name = %s,
                email = %s,
                department_id = %s,
                designation = %s,
                joining_date = %s,
                employee_status = %s,
                user_id = %s
            WHERE employee_id = %s
        """
        params = (full_name, email, department_id, designation, joining_date, employee_status, user_id, id)
        execute_query(sql, params, commit=True)
        
        log_audit(session.get("user_id"), "EMPLOYEE_UPDATE", f"Updated employee {full_name} ({employee['employee_code']})")
        flash(f"Employee '{full_name}' updated successfully.", "success")
        return redirect(url_for("employees.employees_list"))
        
    return render_template("employees.html", action="edit", employee=employee, departments=departments, unlinked_users=unlinked_users)

@employee_bp.route("/employees/delete/<int:id>", methods=["POST"])
@admin_required
def delete_employee(id):
    employee = execute_query("SELECT * FROM employees WHERE employee_id = %s", (id,), fetch_one=True)
    if not employee:
        flash("Employee not found.", "danger")
        return redirect(url_for("employees.employees_list"))
        
    # Check active asset assignments
    active_assets = execute_query(
        "SELECT COUNT(*) AS c FROM asset_assignments WHERE employee_id = %s AND assignment_status = 'Assigned'",
        (id,),
        fetch_one=True
    )
    if active_assets and active_assets["c"] > 0:
        flash(f"Cannot delete employee '{employee['full_name']}': {active_assets['c']} active asset(s) are assigned to them. Return assets first.", "danger")
        return redirect(url_for("employees.employees_list"))
        
    # Check active license assignments
    active_licenses = execute_query(
        "SELECT COUNT(*) AS c FROM license_assignments WHERE employee_id = %s AND assignment_status = 'Assigned'",
        (id,),
        fetch_one=True
    )
    if active_licenses and active_licenses["c"] > 0:
        flash(f"Cannot delete employee '{employee['full_name']}': {active_licenses['c']} active software license seat(s) are allocated to them. Return licenses first.", "danger")
        return redirect(url_for("employees.employees_list"))

    with get_db_cursor(commit=True) as (cursor, _):
        cursor.execute("DELETE FROM asset_assignments WHERE employee_id = %s", (id,))
        cursor.execute("DELETE FROM license_assignments WHERE employee_id = %s", (id,))
        cursor.execute("DELETE FROM employees WHERE employee_id = %s", (id,))
        
    log_audit(session.get("user_id"), "EMPLOYEE_DELETE", f"Deleted employee record: {employee['full_name']} (ID: {id})")
    flash(f"Employee '{employee['full_name']}' deleted successfully.", "success")
    return redirect(url_for("employees.employees_list"))
