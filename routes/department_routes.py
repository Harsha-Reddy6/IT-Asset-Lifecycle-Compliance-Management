from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import execute_query
from utils.auth import login_required, admin_required
from utils.validators import validate_non_empty
from utils.helpers import paginate
from services.audit_service import log_audit

department_bp = Blueprint("departments", __name__)

@department_bp.route("/departments")
@login_required
def departments_list():
    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)
    
    where_sql = "1=1"
    params = []
    if search:
        where_sql = "(department_name LIKE %s OR description LIKE %s)"
        s_term = f"%{search}%"
        params = [s_term, s_term]
        
    count_sql = f"SELECT COUNT(*) AS total FROM departments WHERE {where_sql}"
    count_row = execute_query(count_sql, tuple(params), fetch_one=True)
    total_items = count_row["total"] if count_row else 0
    
    pagination = paginate(total_items, page, 10)
    
    data_sql = f"""
        SELECT 
            d.*,
            (SELECT COUNT(*) FROM employees e WHERE e.department_id = d.department_id) AS employee_count
        FROM departments d
        WHERE {where_sql}
        ORDER BY d.department_name ASC
        LIMIT %s OFFSET %s
    """
    data_params = list(params) + [pagination["per_page"], pagination["offset"]]
    departments = execute_query(data_sql, tuple(data_params), fetch_all=True)
    
    return render_template(
        "departments.html",
        departments=departments,
        pagination=pagination,
        search=search
    )

@department_bp.route("/departments/add", methods=["GET", "POST"])
@admin_required
def add_department():
    if request.method == "POST":
        name = request.form.get("department_name", "").strip()
        description = request.form.get("description", "").strip() or None
        
        valid, err = validate_non_empty(name, "Department Name")
        if not valid:
            flash(err, "danger")
            return render_template("departments.html", action="add", form=request.form)
            
        existing = execute_query("SELECT department_id FROM departments WHERE department_name = %s", (name,), fetch_one=True)
        if existing:
            flash(f"Department '{name}' already exists.", "danger")
            return render_template("departments.html", action="add", form=request.form)
            
        sql = "INSERT INTO departments (department_name, description) VALUES (%s, %s)"
        new_id = execute_query(sql, (name, description), commit=True, return_id=True)
        
        log_audit(session.get("user_id"), "DEPARTMENT_CREATE", f"Created department '{name}' (ID: {new_id})")
        flash(f"Department '{name}' created successfully.", "success")
        return redirect(url_for("departments.departments_list"))
        
    return render_template("departments.html", action="add")

@department_bp.route("/departments/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_department(id):
    department = execute_query("SELECT * FROM departments WHERE department_id = %s", (id,), fetch_one=True)
    if not department:
        flash("Department not found.", "danger")
        return redirect(url_for("departments.departments_list"))
        
    if request.method == "POST":
        name = request.form.get("department_name", "").strip()
        description = request.form.get("description", "").strip() or None
        
        valid, err = validate_non_empty(name, "Department Name")
        if not valid:
            flash(err, "danger")
            return render_template("departments.html", action="edit", department=department)
            
        existing = execute_query(
            "SELECT department_id FROM departments WHERE department_name = %s AND department_id != %s",
            (name, id),
            fetch_one=True
        )
        if existing:
            flash(f"Department name '{name}' is already used by another department.", "danger")
            return render_template("departments.html", action="edit", department=department)
            
        sql = "UPDATE departments SET department_name = %s, description = %s WHERE department_id = %s"
        execute_query(sql, (name, description, id), commit=True)
        
        log_audit(session.get("user_id"), "DEPARTMENT_UPDATE", f"Updated department '{name}' (ID: {id})")
        flash(f"Department '{name}' updated successfully.", "success")
        return redirect(url_for("departments.departments_list"))
        
    return render_template("departments.html", action="edit", department=department)

@department_bp.route("/departments/delete/<int:id>", methods=["POST"])
@admin_required
def delete_department(id):
    department = execute_query("SELECT * FROM departments WHERE department_id = %s", (id,), fetch_one=True)
    if not department:
        flash("Department not found.", "danger")
        return redirect(url_for("departments.departments_list"))
        
    # Check if employees are assigned to this department
    emp_count = execute_query("SELECT COUNT(*) AS c FROM employees WHERE department_id = %s", (id,), fetch_one=True)
    if emp_count and emp_count["c"] > 0:
        # We can dissociate employees or prevent deletion
        execute_query("UPDATE employees SET department_id = NULL WHERE department_id = %s", (id,), commit=True)
        
    execute_query("DELETE FROM departments WHERE department_id = %s", (id,), commit=True)
    log_audit(session.get("user_id"), "DEPARTMENT_DELETE", f"Deleted department '{department['department_name']}' (ID: {id})")
    flash(f"Department '{department['department_name']}' deleted.", "success")
    return redirect(url_for("departments.departments_list"))
