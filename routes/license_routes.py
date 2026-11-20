from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import execute_query
from utils.auth import login_required, admin_required
from utils.validators import validate_positive_int, validate_positive_number
from services.license_service import get_licenses, get_license_by_id, create_license, update_license

license_bp = Blueprint("licenses", __name__)

@license_bp.route("/licenses")
@login_required
def licenses_list():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    page = request.args.get("page", 1, type=int)
    
    licenses, pagination = get_licenses(search=search, status=status, page=page, per_page=10)
    
    software_list = execute_query("SELECT software_id, software_name, version FROM software ORDER BY software_name", fetch_all=True)
    vendors = execute_query("SELECT vendor_id, vendor_name FROM vendors ORDER BY vendor_name", fetch_all=True)
    
    return render_template(
        "licenses.html",
        licenses=licenses,
        pagination=pagination,
        software_list=software_list,
        vendors=vendors,
        search=search,
        selected_status=status
    )

@license_bp.route("/licenses/add", methods=["GET", "POST"])
@admin_required
def add_license():
    software_list = execute_query("SELECT software_id, software_name, version FROM software ORDER BY software_name", fetch_all=True)
    vendors = execute_query("SELECT vendor_id, vendor_name FROM vendors ORDER BY vendor_name", fetch_all=True)
    
    if request.method == "POST":
        software_id = request.form.get("software_id", type=int)
        vendor_id = request.form.get("vendor_id", type=int) or None
        license_key = request.form.get("license_key", "").strip() or None
        total_licenses = request.form.get("total_licenses", 1)
        purchase_date = request.form.get("purchase_date") or None
        expiry_date = request.form.get("expiry_date") or None
        license_cost = request.form.get("license_cost") or None
        license_status = request.form.get("license_status", "Active")
        
        if not software_id:
            flash("Please select software.", "danger")
            return render_template("licenses.html", action="add", software_list=software_list, vendors=vendors, form=request.form)
            
        valid, err, total_val = validate_positive_int(total_licenses, "Total Licenses", allow_zero=False)
        if not valid:
            flash(err, "danger")
            return render_template("licenses.html", action="add", software_list=software_list, vendors=vendors, form=request.form)
            
        if license_cost:
            valid, err, cost_val = validate_positive_number(license_cost, "License Cost")
            if not valid:
                flash(err, "danger")
                return render_template("licenses.html", action="add", software_list=software_list, vendors=vendors, form=request.form)
            license_cost = cost_val

        try:
            data = {
                "software_id": software_id,
                "vendor_id": vendor_id,
                "license_key": license_key,
                "total_licenses": total_val,
                "purchase_date": purchase_date,
                "expiry_date": expiry_date,
                "license_cost": license_cost,
                "license_status": license_status
            }
            create_license(data, session.get("user_id"))
            flash("Software license created successfully.", "success")
            return redirect(url_for("licenses.licenses_list"))
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("licenses.html", action="add", software_list=software_list, vendors=vendors, form=request.form)
            
    return render_template("licenses.html", action="add", software_list=software_list, vendors=vendors)

@license_bp.route("/licenses/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_license(id):
    license_item = get_license_by_id(id)
    if not license_item:
        flash("License not found.", "danger")
        return redirect(url_for("licenses.licenses_list"))
        
    software_list = execute_query("SELECT software_id, software_name, version FROM software ORDER BY software_name", fetch_all=True)
    vendors = execute_query("SELECT vendor_id, vendor_name FROM vendors ORDER BY vendor_name", fetch_all=True)
    
    if request.method == "POST":
        software_id = request.form.get("software_id", type=int)
        vendor_id = request.form.get("vendor_id", type=int) or None
        license_key = request.form.get("license_key", "").strip() or None
        total_licenses = request.form.get("total_licenses")
        purchase_date = request.form.get("purchase_date") or None
        expiry_date = request.form.get("expiry_date") or None
        license_cost = request.form.get("license_cost") or None
        license_status = request.form.get("license_status", license_item["license_status"])
        
        valid, err, total_val = validate_positive_int(total_licenses, "Total Licenses", allow_zero=False)
        if not valid:
            flash(err, "danger")
            return render_template("licenses.html", action="edit", license=license_item, software_list=software_list, vendors=vendors)
            
        if license_cost:
            valid, err, cost_val = validate_positive_number(license_cost, "License Cost")
            if not valid:
                flash(err, "danger")
                return render_template("licenses.html", action="edit", license=license_item, software_list=software_list, vendors=vendors)
            license_cost = cost_val
            
        try:
            data = {
                "software_id": software_id,
                "vendor_id": vendor_id,
                "license_key": license_key,
                "total_licenses": total_val,
                "purchase_date": purchase_date,
                "expiry_date": expiry_date,
                "license_cost": license_cost,
                "license_status": license_status
            }
            update_license(id, data, session.get("user_id"))
            flash("Software license updated successfully.", "success")
            return redirect(url_for("licenses.licenses_list"))
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("licenses.html", action="edit", license=license_item, software_list=software_list, vendors=vendors)

    return render_template("licenses.html", action="edit", license=license_item, software_list=software_list, vendors=vendors)
