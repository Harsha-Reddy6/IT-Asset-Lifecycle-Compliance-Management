from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import execute_query
from utils.auth import login_required, admin_required
from utils.validators import validate_non_empty
from utils.helpers import paginate
from services.audit_service import log_audit

category_bp = Blueprint("categories", __name__)

@category_bp.route("/categories")
@login_required
def categories_list():
    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)
    
    where_sql = "1=1"
    params = []
    if search:
        where_sql = "(category_name LIKE %s OR description LIKE %s)"
        s_term = f"%{search}%"
        params = [s_term, s_term]
        
    count_sql = f"SELECT COUNT(*) AS total FROM asset_categories WHERE {where_sql}"
    count_row = execute_query(count_sql, tuple(params), fetch_one=True)
    total_items = count_row["total"] if count_row else 0
    
    pagination = paginate(total_items, page, 10)
    
    data_sql = f"""
        SELECT 
            c.*,
            (SELECT COUNT(*) FROM assets a WHERE a.category_id = c.category_id) AS asset_count
        FROM asset_categories c
        WHERE {where_sql}
        ORDER BY c.category_name ASC
        LIMIT %s OFFSET %s
    """
    data_params = list(params) + [pagination["per_page"], pagination["offset"]]
    categories = execute_query(data_sql, tuple(data_params), fetch_all=True)
    
    return render_template(
        "categories.html",
        categories=categories,
        pagination=pagination,
        search=search
    )

@category_bp.route("/categories/add", methods=["GET", "POST"])
@admin_required
def add_category():
    if request.method == "POST":
        name = request.form.get("category_name", "").strip()
        description = request.form.get("description", "").strip() or None
        
        valid, err = validate_non_empty(name, "Category Name")
        if not valid:
            flash(err, "danger")
            return render_template("categories.html", action="add", form=request.form)
            
        existing = execute_query("SELECT category_id FROM asset_categories WHERE category_name = %s", (name,), fetch_one=True)
        if existing:
            flash(f"Category '{name}' already exists.", "danger")
            return render_template("categories.html", action="add", form=request.form)
            
        sql = "INSERT INTO asset_categories (category_name, description) VALUES (%s, %s)"
        new_id = execute_query(sql, (name, description), commit=True, return_id=True)
        
        log_audit(session.get("user_id"), "CATEGORY_CREATE", f"Created category '{name}' (ID: {new_id})")
        flash(f"Category '{name}' created successfully.", "success")
        return redirect(url_for("categories.categories_list"))
        
    return render_template("categories.html", action="add")

@category_bp.route("/categories/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_category(id):
    category = execute_query("SELECT * FROM asset_categories WHERE category_id = %s", (id,), fetch_one=True)
    if not category:
        flash("Category not found.", "danger")
        return redirect(url_for("categories.categories_list"))
        
    if request.method == "POST":
        name = request.form.get("category_name", "").strip()
        description = request.form.get("description", "").strip() or None
        
        valid, err = validate_non_empty(name, "Category Name")
        if not valid:
            flash(err, "danger")
            return render_template("categories.html", action="edit", category=category)
            
        existing = execute_query(
            "SELECT category_id FROM asset_categories WHERE category_name = %s AND category_id != %s",
            (name, id),
            fetch_one=True
        )
        if existing:
            flash(f"Category name '{name}' is already used by another category.", "danger")
            return render_template("categories.html", action="edit", category=category)
            
        sql = "UPDATE asset_categories SET category_name = %s, description = %s WHERE category_id = %s"
        execute_query(sql, (name, description, id), commit=True)
        
        log_audit(session.get("user_id"), "CATEGORY_UPDATE", f"Updated category '{name}' (ID: {id})")
        flash(f"Category '{name}' updated successfully.", "success")
        return redirect(url_for("categories.categories_list"))
        
    return render_template("categories.html", action="edit", category=category)

@category_bp.route("/categories/delete/<int:id>", methods=["POST"])
@admin_required
def delete_category(id):
    category = execute_query("SELECT * FROM asset_categories WHERE category_id = %s", (id,), fetch_one=True)
    if not category:
        flash("Category not found.", "danger")
        return redirect(url_for("categories.categories_list"))
        
    # Unlink assets referencing this category
    execute_query("UPDATE assets SET category_id = NULL WHERE category_id = %s", (id,), commit=True)
    execute_query("DELETE FROM asset_categories WHERE category_id = %s", (id,), commit=True)
    
    log_audit(session.get("user_id"), "CATEGORY_DELETE", f"Deleted category '{category['category_name']}' (ID: {id})")
    flash(f"Category '{category['category_name']}' deleted.", "success")
    return redirect(url_for("categories.categories_list"))
