from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import execute_query
from utils.auth import login_required, admin_required
from utils.validators import validate_non_empty
from utils.helpers import paginate
from services.audit_service import log_audit

software_bp = Blueprint("software", __name__)

@software_bp.route("/software")
@login_required
def software_list():
    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)
    
    where_sql = "1=1"
    params = []
    if search:
        where_sql = "(software_name LIKE %s OR publisher LIKE %s OR software_category LIKE %s)"
        s_term = f"%{search}%"
        params = [s_term, s_term, s_term]
        
    count_sql = f"SELECT COUNT(*) AS total FROM software WHERE {where_sql}"
    count_row = execute_query(count_sql, tuple(params), fetch_one=True)
    total_items = count_row["total"] if count_row else 0
    
    pagination = paginate(total_items, page, 10)
    
    data_sql = f"""
        SELECT 
            s.*,
            (SELECT COUNT(*) FROM software_licenses sl WHERE sl.software_id = s.software_id) AS license_count,
            (SELECT COALESCE(SUM(sl.total_licenses), 0) FROM software_licenses sl WHERE sl.software_id = s.software_id) AS total_seats
        FROM software s
        WHERE {where_sql}
        ORDER BY s.software_name ASC
        LIMIT %s OFFSET %s
    """
    data_params = list(params) + [pagination["per_page"], pagination["offset"]]
    software = execute_query(data_sql, tuple(data_params), fetch_all=True)
    
    return render_template(
        "software.html",
        software=software,
        pagination=pagination,
        search=search
    )

@software_bp.route("/software/add", methods=["GET", "POST"])
@admin_required
def add_software():
    if request.method == "POST":
        name = request.form.get("software_name", "").strip()
        publisher = request.form.get("publisher", "").strip() or None
        category = request.form.get("software_category", "").strip() or None
        version = request.form.get("version", "").strip() or None
        
        valid, err = validate_non_empty(name, "Software Name")
        if not valid:
            flash(err, "danger")
            return render_template("software.html", action="add", form=request.form)
            
        sql = """
            INSERT INTO software (software_name, publisher, software_category, version)
            VALUES (%s, %s, %s, %s)
        """
        new_id = execute_query(sql, (name, publisher, category, version), commit=True, return_id=True)
        
        log_audit(session.get("user_id"), "SOFTWARE_CREATE", f"Created software entry '{name}' (ID: {new_id})")
        flash(f"Software '{name}' added successfully.", "success")
        return redirect(url_for("software.software_list"))
        
    return render_template("software.html", action="add")

@software_bp.route("/software/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_software(id):
    item = execute_query("SELECT * FROM software WHERE software_id = %s", (id,), fetch_one=True)
    if not item:
        flash("Software entry not found.", "danger")
        return redirect(url_for("software.software_list"))
        
    if request.method == "POST":
        name = request.form.get("software_name", "").strip()
        publisher = request.form.get("publisher", "").strip() or None
        category = request.form.get("software_category", "").strip() or None
        version = request.form.get("version", "").strip() or None
        
        valid, err = validate_non_empty(name, "Software Name")
        if not valid:
            flash(err, "danger")
            return render_template("software.html", action="edit", item=item)
            
        sql = """
            UPDATE software SET
                software_name = %s,
                publisher = %s,
                software_category = %s,
                version = %s
            WHERE software_id = %s
        """
        execute_query(sql, (name, publisher, category, version, id), commit=True)
        
        log_audit(session.get("user_id"), "SOFTWARE_UPDATE", f"Updated software '{name}' (ID: {id})")
        flash(f"Software '{name}' updated successfully.", "success")
        return redirect(url_for("software.software_list"))
        
    return render_template("software.html", action="edit", item=item)

@software_bp.route("/software/delete/<int:id>", methods=["POST"])
@admin_required
def delete_software(id):
    item = execute_query("SELECT * FROM software WHERE software_id = %s", (id,), fetch_one=True)
    if not item:
        flash("Software entry not found.", "danger")
        return redirect(url_for("software.software_list"))
        
    # Check if licenses exist
    lic_count = execute_query("SELECT COUNT(*) AS c FROM software_licenses WHERE software_id = %s", (id,), fetch_one=True)
    if lic_count and lic_count["c"] > 0:
        flash(f"Cannot delete '{item['software_name']}': {lic_count['c']} license record(s) exist for this software.", "danger")
        return redirect(url_for("software.software_list"))
        
    execute_query("DELETE FROM software WHERE software_id = %s", (id,), commit=True)
    log_audit(session.get("user_id"), "SOFTWARE_DELETE", f"Deleted software '{item['software_name']}' (ID: {id})")
    flash(f"Software '{item['software_name']}' deleted.", "success")
    return redirect(url_for("software.software_list"))
