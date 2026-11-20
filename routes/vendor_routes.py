from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import execute_query
from utils.auth import login_required, admin_required
from utils.validators import validate_non_empty, validate_email
from utils.helpers import paginate
from services.audit_service import log_audit

vendor_bp = Blueprint("vendors", __name__)

@vendor_bp.route("/vendors")
@login_required
def vendors_list():
    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)
    
    where_sql = "1=1"
    params = []
    if search:
        where_sql = "(vendor_name LIKE %s OR contact_person LIKE %s OR email LIKE %s OR phone LIKE %s)"
        s_term = f"%{search}%"
        params = [s_term, s_term, s_term, s_term]
        
    count_sql = f"SELECT COUNT(*) AS total FROM vendors WHERE {where_sql}"
    count_row = execute_query(count_sql, tuple(params), fetch_one=True)
    total_items = count_row["total"] if count_row else 0
    
    pagination = paginate(total_items, page, 10)
    
    data_sql = f"""
        SELECT 
            v.*,
            (SELECT COUNT(*) FROM assets a WHERE a.vendor_id = v.vendor_id) AS asset_count,
            (SELECT COUNT(*) FROM software_licenses sl WHERE sl.vendor_id = v.vendor_id) AS license_count
        FROM vendors v
        WHERE {where_sql}
        ORDER BY v.vendor_name ASC
        LIMIT %s OFFSET %s
    """
    data_params = list(params) + [pagination["per_page"], pagination["offset"]]
    vendors = execute_query(data_sql, tuple(data_params), fetch_all=True)
    
    return render_template(
        "vendors.html",
        vendors=vendors,
        pagination=pagination,
        search=search
    )

@vendor_bp.route("/vendors/add", methods=["GET", "POST"])
@admin_required
def add_vendor():
    if request.method == "POST":
        name = request.form.get("vendor_name", "").strip()
        contact_person = request.form.get("contact_person", "").strip() or None
        email = request.form.get("email", "").strip() or None
        phone = request.form.get("phone", "").strip() or None
        address = request.form.get("address", "").strip() or None
        
        valid, err = validate_non_empty(name, "Vendor Name")
        if not valid:
            flash(err, "danger")
            return render_template("vendors.html", action="add", form=request.form)
            
        if email:
            valid, err = validate_email(email)
            if not valid:
                flash(err, "danger")
                return render_template("vendors.html", action="add", form=request.form)
                
        sql = """
            INSERT INTO vendors (vendor_name, contact_person, email, phone, address)
            VALUES (%s, %s, %s, %s, %s)
        """
        new_id = execute_query(sql, (name, contact_person, email, phone, address), commit=True, return_id=True)
        
        log_audit(session.get("user_id"), "VENDOR_CREATE", f"Created vendor '{name}' (ID: {new_id})")
        flash(f"Vendor '{name}' added successfully.", "success")
        return redirect(url_for("vendors.vendors_list"))
        
    return render_template("vendors.html", action="add")

@vendor_bp.route("/vendors/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_vendor(id):
    vendor = execute_query("SELECT * FROM vendors WHERE vendor_id = %s", (id,), fetch_one=True)
    if not vendor:
        flash("Vendor not found.", "danger")
        return redirect(url_for("vendors.vendors_list"))
        
    if request.method == "POST":
        name = request.form.get("vendor_name", "").strip()
        contact_person = request.form.get("contact_person", "").strip() or None
        email = request.form.get("email", "").strip() or None
        phone = request.form.get("phone", "").strip() or None
        address = request.form.get("address", "").strip() or None
        
        valid, err = validate_non_empty(name, "Vendor Name")
        if not valid:
            flash(err, "danger")
            return render_template("vendors.html", action="edit", vendor=vendor)
            
        if email:
            valid, err = validate_email(email)
            if not valid:
                flash(err, "danger")
                return render_template("vendors.html", action="edit", vendor=vendor)
                
        sql = """
            UPDATE vendors SET
                vendor_name = %s,
                contact_person = %s,
                email = %s,
                phone = %s,
                address = %s
            WHERE vendor_id = %s
        """
        execute_query(sql, (name, contact_person, email, phone, address, id), commit=True)
        
        log_audit(session.get("user_id"), "VENDOR_UPDATE", f"Updated vendor '{name}' (ID: {id})")
        flash(f"Vendor '{name}' updated successfully.", "success")
        return redirect(url_for("vendors.vendors_list"))
        
    return render_template("vendors.html", action="edit", vendor=vendor)

@vendor_bp.route("/vendors/delete/<int:id>", methods=["POST"])
@admin_required
def delete_vendor(id):
    vendor = execute_query("SELECT * FROM vendors WHERE vendor_id = %s", (id,), fetch_one=True)
    if not vendor:
        flash("Vendor not found.", "danger")
        return redirect(url_for("vendors.vendors_list"))
        
    execute_query("UPDATE assets SET vendor_id = NULL WHERE vendor_id = %s", (id,), commit=True)
    execute_query("UPDATE software_licenses SET vendor_id = NULL WHERE vendor_id = %s", (id,), commit=True)
    execute_query("UPDATE purchase_orders SET vendor_id = NULL WHERE vendor_id = %s", (id,), commit=True)
    execute_query("DELETE FROM vendors WHERE vendor_id = %s", (id,), commit=True)
    
    log_audit(session.get("user_id"), "VENDOR_DELETE", f"Deleted vendor '{vendor['vendor_name']}' (ID: {id})")
    flash(f"Vendor '{vendor['vendor_name']}' deleted.", "success")
    return redirect(url_for("vendors.vendors_list"))
