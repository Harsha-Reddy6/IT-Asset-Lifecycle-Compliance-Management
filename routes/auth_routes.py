from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import execute_query, get_db_cursor
from utils.auth import hash_password, verify_password, login_required
from utils.validators import validate_email, validate_username, validate_password_strength, validate_non_empty
from services.audit_service import log_audit

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard.dashboard_view"))
        
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        
        if not identifier or not password:
            flash("Please enter both username/email and password.", "danger")
            return render_template("login.html", identifier=identifier)
            
        sql = """
            SELECT id, full_name, email, username, password_hash, role
            FROM users
            WHERE username = %s OR email = %s
        """
        user = execute_query(sql, (identifier, identifier), fetch_one=True)
        
        if not user or not verify_password(password, user["password_hash"]):
            flash("Invalid credentials. Please verify your administrator username/email and password.", "danger")
            return render_template("login.html", identifier=identifier)
            
        if user["role"] != "admin":
            flash("Access denied: This portal is restricted to System Administrators only.", "danger")
            return render_template("login.html", identifier=identifier)
            
        # Secure Session-based Login
        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["full_name"] = user["full_name"]
        session["email"] = user["email"]
        session["role"] = user["role"]
        session.permanent = True
        
        log_audit(user["id"], "ADMIN_LOGIN", f"Administrator '{user['username']}' logged in successfully.")
        flash(f"Welcome back, Administrator {user['full_name']}!", "success")
        
        next_page = request.args.get("next")
        if next_page and next_page.startswith("/"):
            return redirect(next_page)
        return redirect(url_for("dashboard.dashboard_view"))
        
    return render_template("login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("dashboard.dashboard_view"))
        
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        # Validations
        valid, err = validate_non_empty(full_name, "Full Name")
        if not valid:
            flash(err, "danger")
            return render_template("register.html", full_name=full_name, email=email, username=username)
            
        valid, err = validate_email(email)
        if not valid:
            flash(err, "danger")
            return render_template("register.html", full_name=full_name, email=email, username=username)
            
        valid, err = validate_username(username)
        if not valid:
            flash(err, "danger")
            return render_template("register.html", full_name=full_name, email=email, username=username)
            
        valid, err = validate_password_strength(password)
        if not valid:
            flash(err, "danger")
            return render_template("register.html", full_name=full_name, email=email, username=username)
            
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html", full_name=full_name, email=email, username=username)
            
        # Check uniqueness
        existing_user = execute_query(
            "SELECT id FROM users WHERE username = %s OR email = %s",
            (username, email),
            fetch_one=True
        )
        if existing_user:
            flash("An account with that username or email already exists.", "danger")
            return render_template("register.html", full_name=full_name, email=email, username=username)
            
        # Register user with employee role only (Public registration as admin strictly prohibited)
        pw_hash = hash_password(password)
        
        with get_db_cursor(commit=True) as (cursor, _):
            cursor.execute("""
                INSERT INTO users (full_name, email, username, password_hash, role, created_at)
                VALUES (%s, %s, %s, %s, 'employee', NOW())
            """, (full_name, email, username, pw_hash))
            new_user_id = cursor.lastrowid
            
            # Check or create associated employee record
            cursor.execute("SELECT employee_id FROM employees WHERE email = %s", (email,))
            existing_emp = cursor.fetchone()
            
            if existing_emp:
                cursor.execute("UPDATE employees SET user_id = %s WHERE employee_id = %s", (new_user_id, existing_emp["employee_id"]))
            else:
                emp_code = f"EMP-{new_user_id:04d}"
                cursor.execute("""
                    INSERT INTO employees (user_id, employee_code, full_name, email, employee_status, joining_date)
                    VALUES (%s, %s, %s, %s, 'Active', CURDATE())
                """, (new_user_id, emp_code, full_name, email))
                
        log_audit(new_user_id, "USER_REGISTER", f"Employee registered account with username '{username}'")
        flash("Registration successful! You may now log in.", "success")
        return redirect(url_for("auth.login"))
        
    return render_template("register.html")

@auth_bp.route("/logout")
def logout():
    user_id = session.get("user_id")
    username = session.get("username", "Unknown")
    if user_id:
        log_audit(user_id, "USER_LOGOUT", f"User '{username}' logged out.")
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_id = session["user_id"]
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "update_info":
            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip()
            
            valid, err = validate_non_empty(full_name, "Full Name")
            if not valid:
                flash(err, "danger")
                return redirect(url_for("auth.profile"))
                
            valid, err = validate_email(email)
            if not valid:
                flash(err, "danger")
                return redirect(url_for("auth.profile"))
                
            # Uniqueness check for email
            existing = execute_query(
                "SELECT id FROM users WHERE email = %s AND id != %s",
                (email, user_id),
                fetch_one=True
            )
            if existing:
                flash("This email is already associated with another account.", "danger")
                return redirect(url_for("auth.profile"))
                
            with get_db_cursor(commit=True) as (cursor, _):
                cursor.execute("UPDATE users SET full_name = %s, email = %s WHERE id = %s", (full_name, email, user_id))
                cursor.execute("UPDATE employees SET full_name = %s, email = %s WHERE user_id = %s", (full_name, email, user_id))
                
            session["full_name"] = full_name
            session["email"] = email
            log_audit(user_id, "PROFILE_UPDATE", f"User updated profile details.")
            flash("Profile updated successfully.", "success")
            return redirect(url_for("auth.profile"))
            
        elif action == "change_password":
            current_pw = request.form.get("current_password", "")
            new_pw = request.form.get("new_password", "")
            confirm_new_pw = request.form.get("confirm_new_password", "")
            
            user = execute_query("SELECT password_hash FROM users WHERE id = %s", (user_id,), fetch_one=True)
            if not user or not verify_password(current_pw, user["password_hash"]):
                flash("Current password is incorrect.", "danger")
                return redirect(url_for("auth.profile"))
                
            valid, err = validate_password_strength(new_pw)
            if not valid:
                flash(err, "danger")
                return redirect(url_for("auth.profile"))
                
            if new_pw != confirm_new_pw:
                flash("New passwords do not match.", "danger")
                return redirect(url_for("auth.profile"))
                
            new_hash = hash_password(new_pw)
            execute_query("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user_id), commit=True)
            log_audit(user_id, "PASSWORD_CHANGE", "User successfully changed account password.")
            flash("Password updated successfully.", "success")
            return redirect(url_for("auth.profile"))

    # Fetch user & employee data
    user = execute_query("SELECT * FROM users WHERE id = %s", (user_id,), fetch_one=True)
    employee = execute_query("""
        SELECT e.*, d.department_name
        FROM employees e
        LEFT JOIN departments d ON e.department_id = d.department_id
        WHERE e.user_id = %s
    """, (user_id,), fetch_one=True)
    
    my_assets = []
    my_licenses = []
    if employee:
        emp_id = employee["employee_id"]
        my_assets = execute_query("""
            SELECT aa.assignment_id, aa.assigned_date, aa.remarks, a.*, c.category_name
            FROM asset_assignments aa
            JOIN assets a ON aa.asset_id = a.asset_id
            LEFT JOIN asset_categories c ON a.category_id = c.category_id
            WHERE aa.employee_id = %s AND aa.assignment_status = 'Assigned'
            ORDER BY aa.assigned_date DESC
        """, (emp_id,), fetch_all=True)
        
        my_licenses = execute_query("""
            SELECT la.license_assignment_id, la.assigned_date, s.software_name, s.publisher, s.version, sl.license_key, sl.expiry_date
            FROM license_assignments la
            JOIN software_licenses sl ON la.license_id = sl.license_id
            JOIN software s ON sl.software_id = s.software_id
            WHERE la.employee_id = %s AND la.assignment_status = 'Assigned'
            ORDER BY la.assigned_date DESC
        """, (emp_id,), fetch_all=True)
        
    return render_template(
        "profile.html",
        user=user,
        employee=employee,
        my_assets=my_assets,
        my_licenses=my_licenses
    )
