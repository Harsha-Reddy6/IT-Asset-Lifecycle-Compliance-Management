from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import execute_query
from utils.auth import login_required, admin_required
from services.asset_service import get_assignments, assign_asset, return_asset

assignment_bp = Blueprint("assignments", __name__)

@assignment_bp.route("/assignments")
@login_required
def assignments_list():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    page = request.args.get("page", 1, type=int)
    
    assignments, pagination = get_assignments(search=search, status=status, page=page, per_page=10)
    
    # Available assets for assignment modal/form
    available_assets = execute_query(
        "SELECT asset_id, asset_code, asset_name, brand, model_number FROM assets WHERE asset_status = 'Available' ORDER BY asset_name",
        fetch_all=True
    )
    # Active employees
    active_employees = execute_query(
        "SELECT employee_id, employee_code, full_name, email FROM employees WHERE employee_status = 'Active' ORDER BY full_name",
        fetch_all=True
    )
    
    return render_template(
        "assignments.html",
        assignments=assignments,
        pagination=pagination,
        search=search,
        selected_status=status,
        available_assets=available_assets,
        active_employees=active_employees
    )

@assignment_bp.route("/assignments/add", methods=["GET", "POST"])
@admin_required
def add_assignment():
    available_assets = execute_query(
        "SELECT asset_id, asset_code, asset_name, brand, model_number FROM assets WHERE asset_status = 'Available' ORDER BY asset_name",
        fetch_all=True
    )
    active_employees = execute_query(
        "SELECT employee_id, employee_code, full_name, email FROM employees WHERE employee_status = 'Active' ORDER BY full_name",
        fetch_all=True
    )
    
    if request.method == "POST":
        asset_id = request.form.get("asset_id", type=int)
        employee_id = request.form.get("employee_id", type=int)
        remarks = request.form.get("remarks", "").strip()
        
        if not asset_id:
            flash("Please select an asset to assign.", "danger")
            return render_template("assignments.html", action="add", available_assets=available_assets, active_employees=active_employees)
            
        if not employee_id:
            flash("Please select an employee.", "danger")
            return render_template("assignments.html", action="add", available_assets=available_assets, active_employees=active_employees)
            
        try:
            assign_asset(asset_id, employee_id, remarks, session.get("user_id"))
            flash("Asset allocated successfully.", "success")
            return redirect(url_for("assignments.assignments_list"))
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("assignments.html", action="add", available_assets=available_assets, active_employees=active_employees, form=request.form)
            
    return render_template("assignments.html", action="add", available_assets=available_assets, active_employees=active_employees)

@assignment_bp.route("/assignments/return/<int:id>", methods=["POST"])
@admin_required
def return_asset_route(id):
    remarks = request.form.get("remarks", "").strip()
    try:
        return_asset(id, remarks, session.get("user_id"))
        flash("Asset returned successfully and updated to 'Available'.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("assignments.assignments_list"))
