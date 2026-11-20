import os
from flask import Flask, redirect, url_for, session, render_template, request, flash, abort
from config import Config
from database import check_db_health
from utils.auth import generate_csrf_token, validate_csrf_token
from utils.helpers import format_currency, format_date

# Import Blueprints
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.employee_routes import employee_bp
from routes.department_routes import department_bp
from routes.asset_routes import asset_bp
from routes.category_routes import category_bp
from routes.assignment_routes import assignment_bp
from routes.vendor_routes import vendor_bp
from routes.software_routes import software_bp
from routes.license_routes import license_bp
from routes.license_assignment_routes import license_assignment_bp
from routes.maintenance_routes import maintenance_bp
from routes.purchase_order_routes import purchase_order_bp
from routes.compliance_routes import compliance_bp
from routes.report_routes import report_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # CSRF Protection Hook
    @app.before_request
    def check_csrf():
        if app.config.get("TESTING"):
            return
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            # Check CSRF token from form or header
            token = request.form.get("csrf_token") or request.headers.get("X-CSRFToken")
            if not token or not validate_csrf_token(token):
                # If session has no token yet or token mismatched
                flash("Your security token has expired or is invalid. Please try again.", "warning")
                return redirect(request.referrer or url_for("dashboard.dashboard_view"))

    # Context Processors for Jinja2 templates
    @app.context_processor
    def inject_utilities():
        return {
            "csrf_token": generate_csrf_token,
            "format_currency": format_currency,
            "format_date": format_date,
            "current_user": {
                "id": session.get("user_id"),
                "username": session.get("username"),
                "full_name": session.get("full_name"),
                "email": session.get("email"),
                "role": session.get("role")
            }
        }
        
    # Root Route
    @app.route("/")
    def index():
        if session.get("user_id"):
            return redirect(url_for("dashboard.dashboard_view"))
        return redirect(url_for("auth.login"))

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(department_bp)
    app.register_blueprint(asset_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(assignment_bp)
    app.register_blueprint(vendor_bp)
    app.register_blueprint(software_bp)
    app.register_blueprint(license_bp)
    app.register_blueprint(license_assignment_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(purchase_order_bp)
    app.register_blueprint(compliance_bp)
    app.register_blueprint(report_bp)
    
    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("base.html", error_title="404 - Page Not Found", error_message="The requested page could not be located."), 404
        
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("base.html", error_title="403 - Forbidden", error_message="You do not have permission to access this resource."), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template("base.html", error_title="500 - Server Error", error_message="An unexpected server error occurred. Please contact IT support."), 500

    return app

app = create_app()

if __name__ == "__main__":
    print("==================================================================")
    print(" Intelligent IT Asset Lifecycle & License Compliance Platform")
    print(" Server: Flask Traditional Multi-Page Web Application")
    print("==================================================================")
    db_ok = check_db_health()
    if db_ok:
        print(" [OK] Connected to MySQL database:", Config.DB_NAME)
    else:
        print(" [WARNING] Could not connect to MySQL database:", Config.DB_NAME)
    print(" Application URL: http://127.0.0.1:5000/")
    print("==================================================================")
    app.run(host="127.0.0.1", port=5000, debug=True)
