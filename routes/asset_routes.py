from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import execute_query
from utils.auth import login_required, admin_required
from utils.validators import validate_non_empty, validate_date, validate_positive_number
from services.asset_service import (
    get_assets, get_asset_by_id, create_asset, update_asset,
    delete_asset, get_asset_assignment_history, get_asset_maintenance_history
)

asset_bp = Blueprint("assets", __name__)

@asset_bp.route("/assets")
@login_required
def assets_list():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    cat_id = request.args.get("category_id", type=int)
    page = request.args.get("page", 1, type=int)
    
    assets, pagination = get_assets(search=search, status=status, category_id=cat_id, page=page, per_page=10)
    
    categories = execute_query("SELECT category_id, category_name FROM asset_categories ORDER BY category_name", fetch_all=True)
    vendors = execute_query("SELECT vendor_id, vendor_name FROM vendors ORDER BY vendor_name", fetch_all=True)
    
    return render_template(
        "assets.html",
        assets=assets,
        pagination=pagination,
        categories=categories,
        vendors=vendors,
        search=search,
        selected_status=status,
        selected_category=cat_id
    )

@asset_bp.route("/assets/add", methods=["GET", "POST"])
@admin_required
def add_asset():
    categories = execute_query("SELECT category_id, category_name FROM asset_categories ORDER BY category_name", fetch_all=True)
    vendors = execute_query("SELECT vendor_id, vendor_name FROM vendors ORDER BY vendor_name", fetch_all=True)
    
    if request.method == "POST":
        asset_name = request.form.get("asset_name", "").strip()
        asset_code = request.form.get("asset_code", "").strip()
        category_id = request.form.get("category_id") or None
        vendor_id = request.form.get("vendor_id") or None
        brand = request.form.get("brand", "").strip()
        model_number = request.form.get("model_number", "").strip()
        serial_number = request.form.get("serial_number", "").strip()
        purchase_date = request.form.get("purchase_date") or None
        purchase_cost = request.form.get("purchase_cost") or None
        warranty_expiry = request.form.get("warranty_expiry") or None
        location = request.form.get("location", "").strip()
        asset_status = request.form.get("asset_status", "Available")
        
        valid, err = validate_non_empty(asset_name, "Asset Name")
        if not valid:
            flash(err, "danger")
            return render_template("assets.html", action="add", categories=categories, vendors=vendors, form=request.form)
            
        if purchase_cost:
            valid, err, cost_val = validate_positive_number(purchase_cost, "Purchase Cost")
            if not valid:
                flash(err, "danger")
                return render_template("assets.html", action="add", categories=categories, vendors=vendors, form=request.form)
            purchase_cost = cost_val
            
        try:
            data = {
                "asset_name": asset_name,
                "asset_code": asset_code,
                "category_id": category_id,
                "vendor_id": vendor_id,
                "brand": brand,
                "model_number": model_number,
                "serial_number": serial_number,
                "purchase_date": purchase_date,
                "purchase_cost": purchase_cost,
                "warranty_expiry": warranty_expiry,
                "location": location,
                "asset_status": asset_status
            }
            create_asset(data, session.get("user_id"))
            flash(f"Asset '{asset_name}' added successfully.", "success")
            return redirect(url_for("assets.assets_list"))
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("assets.html", action="add", categories=categories, vendors=vendors, form=request.form)
            
    return render_template("assets.html", action="add", categories=categories, vendors=vendors)

@asset_bp.route("/assets/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_asset(id):
    asset = get_asset_by_id(id)
    if not asset:
        flash("Asset not found.", "danger")
        return redirect(url_for("assets.assets_list"))
        
    categories = execute_query("SELECT category_id, category_name FROM asset_categories ORDER BY category_name", fetch_all=True)
    vendors = execute_query("SELECT vendor_id, vendor_name FROM vendors ORDER BY vendor_name", fetch_all=True)
    
    if request.method == "POST":
        asset_name = request.form.get("asset_name", "").strip()
        category_id = request.form.get("category_id") or None
        vendor_id = request.form.get("vendor_id") or None
        brand = request.form.get("brand", "").strip()
        model_number = request.form.get("model_number", "").strip()
        serial_number = request.form.get("serial_number", "").strip()
        purchase_date = request.form.get("purchase_date") or None
        purchase_cost = request.form.get("purchase_cost") or None
        warranty_expiry = request.form.get("warranty_expiry") or None
        location = request.form.get("location", "").strip()
        asset_status = request.form.get("asset_status", asset["asset_status"])
        
        valid, err = validate_non_empty(asset_name, "Asset Name")
        if not valid:
            flash(err, "danger")
            return render_template("assets.html", action="edit", asset=asset, categories=categories, vendors=vendors)
            
        if purchase_cost:
            valid, err, cost_val = validate_positive_number(purchase_cost, "Purchase Cost")
            if not valid:
                flash(err, "danger")
                return render_template("assets.html", action="edit", asset=asset, categories=categories, vendors=vendors)
            purchase_cost = cost_val
            
        try:
            data = {
                "asset_name": asset_name,
                "category_id": category_id,
                "vendor_id": vendor_id,
                "brand": brand,
                "model_number": model_number,
                "serial_number": serial_number,
                "purchase_date": purchase_date,
                "purchase_cost": purchase_cost,
                "warranty_expiry": warranty_expiry,
                "location": location,
                "asset_status": asset_status
            }
            update_asset(id, data, session.get("user_id"))
            flash(f"Asset '{asset_name}' updated successfully.", "success")
            return redirect(url_for("assets.assets_list"))
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("assets.html", action="edit", asset=asset, categories=categories, vendors=vendors)
            
    return render_template("assets.html", action="edit", asset=asset, categories=categories, vendors=vendors)

@asset_bp.route("/assets/delete/<int:id>", methods=["POST"])
@admin_required
def delete_asset_route(id):
    try:
        delete_asset(id, session.get("user_id"))
        flash("Asset deleted successfully.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("assets.assets_list"))

@asset_bp.route("/assets/view/<int:id>")
@login_required
def view_asset(id):
    asset = get_asset_by_id(id)
    if not asset:
        flash("Asset not found.", "danger")
        return redirect(url_for("assets.assets_list"))
        
    assignment_history = get_asset_assignment_history(id)
    maintenance_history = get_asset_maintenance_history(id)
    
    return render_template(
        "assets.html",
        action="view",
        asset=asset,
        assignment_history=assignment_history,
        maintenance_history=maintenance_history
    )
