from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import execute_query
from utils.auth import login_required, admin_required
from utils.validators import validate_non_empty, validate_positive_number
from utils.helpers import paginate
from services.audit_service import log_audit

purchase_order_bp = Blueprint("purchase_orders", __name__)

@purchase_order_bp.route("/purchase-orders")
@login_required
def purchase_orders_list():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    page = request.args.get("page", 1, type=int)
    
    where_clauses = ["1=1"]
    params = []
    
    if search:
        s_term = f"%{search}%"
        where_clauses.append("(po.order_number LIKE %s OR v.vendor_name LIKE %s)")
        params.extend([s_term, s_term])
        
    if status:
        where_clauses.append("po.order_status = %s")
        params.append(status)
        
    where_sql = " AND ".join(where_clauses)
    
    count_sql = f"""
        SELECT COUNT(*) AS total 
        FROM purchase_orders po
        LEFT JOIN vendors v ON po.vendor_id = v.vendor_id
        WHERE {where_sql}
    """
    count_row = execute_query(count_sql, tuple(params), fetch_one=True)
    total_items = count_row["total"] if count_row else 0
    
    pagination = paginate(total_items, page, 10)
    
    data_sql = f"""
        SELECT 
            po.*,
            v.vendor_name,
            v.contact_person,
            v.email AS vendor_email
        FROM purchase_orders po
        LEFT JOIN vendors v ON po.vendor_id = v.vendor_id
        WHERE {where_sql}
        ORDER BY po.purchase_order_id DESC
        LIMIT %s OFFSET %s
    """
    data_params = list(params) + [pagination["per_page"], pagination["offset"]]
    orders = execute_query(data_sql, tuple(data_params), fetch_all=True)
    
    vendors = execute_query("SELECT vendor_id, vendor_name FROM vendors ORDER BY vendor_name", fetch_all=True)
    
    return render_template(
        "purchase_orders.html",
        orders=orders,
        pagination=pagination,
        vendors=vendors,
        search=search,
        selected_status=status
    )

@purchase_order_bp.route("/purchase-orders/add", methods=["GET", "POST"])
@admin_required
def add_purchase_order():
    vendors = execute_query("SELECT vendor_id, vendor_name FROM vendors ORDER BY vendor_name", fetch_all=True)
    
    if request.method == "POST":
        order_number = request.form.get("order_number", "").strip()
        vendor_id = request.form.get("vendor_id", type=int) or None
        order_date = request.form.get("order_date") or None
        total_amount = request.form.get("total_amount")
        order_status = request.form.get("order_status", "Pending")
        
        valid, err = validate_non_empty(order_number, "Order Number")
        if not valid:
            flash(err, "danger")
            return render_template("purchase_orders.html", action="add", vendors=vendors, form=request.form)
            
        existing = execute_query("SELECT purchase_order_id FROM purchase_orders WHERE order_number = %s", (order_number,), fetch_one=True)
        if existing:
            flash(f"Purchase order number '{order_number}' already exists.", "danger")
            return render_template("purchase_orders.html", action="add", vendors=vendors, form=request.form)
            
        amount_val = 0.0
        if total_amount:
            valid, err, parsed = validate_positive_number(total_amount, "Total Amount")
            if not valid:
                flash(err, "danger")
                return render_template("purchase_orders.html", action="add", vendors=vendors, form=request.form)
            amount_val = parsed
            
        sql = """
            INSERT INTO purchase_orders (vendor_id, order_number, order_date, total_amount, order_status)
            VALUES (%s, %s, %s, %s, %s)
        """
        new_id = execute_query(sql, (vendor_id, order_number, order_date, amount_val, order_status), commit=True, return_id=True)
        
        log_audit(session.get("user_id"), "PO_CREATE", f"Created purchase order {order_number} (ID: {new_id})")
        flash(f"Purchase order '{order_number}' created successfully.", "success")
        return redirect(url_for("purchase_orders.purchase_orders_list"))
        
    return render_template("purchase_orders.html", action="add", vendors=vendors)

@purchase_order_bp.route("/purchase-orders/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_purchase_order(id):
    order = execute_query("SELECT * FROM purchase_orders WHERE purchase_order_id = %s", (id,), fetch_one=True)
    if not order:
        flash("Purchase order not found.", "danger")
        return redirect(url_for("purchase_orders.purchase_orders_list"))
        
    vendors = execute_query("SELECT vendor_id, vendor_name FROM vendors ORDER BY vendor_name", fetch_all=True)
    
    if request.method == "POST":
        vendor_id = request.form.get("vendor_id", type=int) or None
        order_date = request.form.get("order_date") or None
        total_amount = request.form.get("total_amount")
        order_status = request.form.get("order_status", order["order_status"])
        
        amount_val = 0.0
        if total_amount:
            valid, err, parsed = validate_positive_number(total_amount, "Total Amount")
            if not valid:
                flash(err, "danger")
                return render_template("purchase_orders.html", action="edit", order=order, vendors=vendors)
            amount_val = parsed
            
        sql = """
            UPDATE purchase_orders SET
                vendor_id = %s,
                order_date = %s,
                total_amount = %s,
                order_status = %s
            WHERE purchase_order_id = %s
        """
        execute_query(sql, (vendor_id, order_date, amount_val, order_status, id), commit=True)
        
        log_audit(session.get("user_id"), "PO_UPDATE", f"Updated purchase order {order['order_number']} (Status: {order_status})")
        flash(f"Purchase order '{order['order_number']}' updated successfully.", "success")
        return redirect(url_for("purchase_orders.purchase_orders_list"))
        
    return render_template("purchase_orders.html", action="edit", order=order, vendors=vendors)
