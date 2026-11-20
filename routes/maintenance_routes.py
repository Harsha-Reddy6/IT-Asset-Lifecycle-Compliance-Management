from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import execute_query, get_db_cursor
from utils.auth import login_required, admin_required
from utils.validators import validate_non_empty, validate_positive_number
from utils.helpers import paginate
from services.audit_service import log_audit

maintenance_bp = Blueprint("maintenance", __name__)

@maintenance_bp.route("/maintenance")
@login_required
def maintenance_list():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    page = request.args.get("page", 1, type=int)
    
    where_clauses = ["1=1"]
    params = []
    
    if search:
        s_term = f"%{search}%"
        where_clauses.append("(a.asset_name LIKE %s OR a.asset_code LIKE %s OR m.maintenance_type LIKE %s OR m.description LIKE %s)")
        params.extend([s_term, s_term, s_term, s_term])
        
    if status:
        where_clauses.append("m.maintenance_status = %s")
        params.append(status)
        
    where_sql = " AND ".join(where_clauses)
    
    count_sql = f"""
        SELECT COUNT(*) AS total 
        FROM maintenance_records m
        JOIN assets a ON m.asset_id = a.asset_id
        WHERE {where_sql}
    """
    count_row = execute_query(count_sql, tuple(params), fetch_one=True)
    total_items = count_row["total"] if count_row else 0
    
    pagination = paginate(total_items, page, 10)
    
    data_sql = f"""
        SELECT 
            m.*,
            a.asset_name,
            a.asset_code,
            a.serial_number,
            a.asset_status AS current_asset_status
        FROM maintenance_records m
        JOIN assets a ON m.asset_id = a.asset_id
        WHERE {where_sql}
        ORDER BY m.maintenance_id DESC
        LIMIT %s OFFSET %s
    """
    data_params = list(params) + [pagination["per_page"], pagination["offset"]]
    records = execute_query(data_sql, tuple(data_params), fetch_all=True)
    
    assets = execute_query("SELECT asset_id, asset_code, asset_name FROM assets ORDER BY asset_name", fetch_all=True)
    
    return render_template(
        "maintenance.html",
        records=records,
        pagination=pagination,
        assets=assets,
        search=search,
        selected_status=status
    )

@maintenance_bp.route("/maintenance/add", methods=["GET", "POST"])
@admin_required
def add_maintenance():
    assets = execute_query("SELECT asset_id, asset_code, asset_name FROM assets ORDER BY asset_name", fetch_all=True)
    
    if request.method == "POST":
        asset_id = request.form.get("asset_id", type=int)
        maintenance_type = request.form.get("maintenance_type", "").strip() or None
        maintenance_date = request.form.get("maintenance_date") or None
        cost = request.form.get("cost") or None
        description = request.form.get("description", "").strip() or None
        maintenance_status = request.form.get("maintenance_status", "Pending")
        
        if not asset_id:
            flash("Please select an asset.", "danger")
            return render_template("maintenance.html", action="add", assets=assets, form=request.form)
            
        cost_val = 0.0
        if cost:
            valid, err, parsed_cost = validate_positive_number(cost, "Maintenance Cost")
            if not valid:
                flash(err, "danger")
                return render_template("maintenance.html", action="add", assets=assets, form=request.form)
            cost_val = parsed_cost
            
        with get_db_cursor(commit=True) as (cursor, _):
            cursor.execute("""
                INSERT INTO maintenance_records (asset_id, maintenance_type, maintenance_date, cost, description, maintenance_status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (asset_id, maintenance_type, maintenance_date, cost_val, description, maintenance_status))
            new_id = cursor.lastrowid
            
            # If status is in progress or pending, update asset status to Under Maintenance
            if maintenance_status in ["Pending", "In Progress"]:
                cursor.execute("UPDATE assets SET asset_status = 'Under Maintenance' WHERE asset_id = %s", (asset_id,))
                
        log_audit(session.get("user_id"), "MAINTENANCE_CREATE", f"Logged maintenance record ID {new_id} for asset ID {asset_id}")
        flash("Maintenance record created successfully.", "success")
        return redirect(url_for("maintenance.maintenance_list"))
        
    return render_template("maintenance.html", action="add", assets=assets)

@maintenance_bp.route("/maintenance/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_maintenance(id):
    record = execute_query("""
        SELECT m.*, a.asset_name, a.asset_code 
        FROM maintenance_records m
        JOIN assets a ON m.asset_id = a.asset_id
        WHERE m.maintenance_id = %s
    """, (id,), fetch_one=True)
    
    if not record:
        flash("Maintenance record not found.", "danger")
        return redirect(url_for("maintenance.maintenance_list"))
        
    assets = execute_query("SELECT asset_id, asset_code, asset_name FROM assets ORDER BY asset_name", fetch_all=True)
    
    if request.method == "POST":
        maintenance_type = request.form.get("maintenance_type", "").strip() or None
        maintenance_date = request.form.get("maintenance_date") or None
        cost = request.form.get("cost") or None
        description = request.form.get("description", "").strip() or None
        maintenance_status = request.form.get("maintenance_status", record["maintenance_status"])
        
        cost_val = 0.0
        if cost:
            valid, err, parsed_cost = validate_positive_number(cost, "Maintenance Cost")
            if not valid:
                flash(err, "danger")
                return render_template("maintenance.html", action="edit", record=record, assets=assets)
            cost_val = parsed_cost

        with get_db_cursor(commit=True) as (cursor, _):
            cursor.execute("""
                UPDATE maintenance_records SET
                    maintenance_type = %s,
                    maintenance_date = %s,
                    cost = %s,
                    description = %s,
                    maintenance_status = %s
                WHERE maintenance_id = %s
            """, (maintenance_type, maintenance_date, cost_val, description, maintenance_status, id))
            
            # Asset status update business logic
            asset_id = record["asset_id"]
            if maintenance_status == "Completed":
                # Check active assignment
                cursor.execute(
                    "SELECT assignment_id FROM asset_assignments WHERE asset_id = %s AND assignment_status = 'Assigned'",
                    (asset_id,)
                )
                active = cursor.fetchone()
                if active:
                    cursor.execute("UPDATE assets SET asset_status = 'Assigned' WHERE asset_id = %s", (asset_id,))
                else:
                    cursor.execute("UPDATE assets SET asset_status = 'Available' WHERE asset_id = %s", (asset_id,))
            elif maintenance_status in ["Pending", "In Progress"]:
                cursor.execute("UPDATE assets SET asset_status = 'Under Maintenance' WHERE asset_id = %s", (asset_id,))

        log_audit(session.get("user_id"), "MAINTENANCE_UPDATE", f"Updated maintenance record ID {id} (status: {maintenance_status})")
        flash("Maintenance record updated successfully.", "success")
        return redirect(url_for("maintenance.maintenance_list"))
        
    return render_template("maintenance.html", action="edit", record=record, assets=assets)
