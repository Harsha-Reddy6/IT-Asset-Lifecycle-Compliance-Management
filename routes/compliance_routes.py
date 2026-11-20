from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.auth import login_required, admin_required
from services.compliance_service import run_compliance_scan, get_alerts, resolve_alert, get_compliance_stats

compliance_bp = Blueprint("compliance", __name__)

@compliance_bp.route("/compliance", methods=["GET", "POST"])
@login_required
def compliance_dashboard():
    if request.method == "POST":
        # Admin runs audit scan
        if session.get("role") != "admin":
            flash("Only administrators can initiate full compliance scans.", "danger")
            return redirect(url_for("compliance.compliance_dashboard"))
            
        new_alerts = run_compliance_scan(session.get("user_id"))
        if new_alerts > 0:
            flash(f"Compliance scan completed: {new_alerts} new alert(s) detected.", "warning")
        else:
            flash("Compliance scan completed: No new compliance violations found.", "success")
        return redirect(url_for("compliance.compliance_dashboard"))
        
    status = request.args.get("status", "Open")
    alert_type = request.args.get("type", "All")
    page = request.args.get("page", 1, type=int)
    
    alerts, pagination = get_alerts(status=status, alert_type=alert_type, page=page, per_page=10)
    stats = get_compliance_stats()
    
    return render_template(
        "compliance.html",
        alerts=alerts,
        pagination=pagination,
        stats=stats,
        selected_status=status,
        selected_type=alert_type
    )

@compliance_bp.route("/compliance/resolve/<int:id>", methods=["POST"])
@admin_required
def resolve_alert_route(id):
    try:
        resolve_alert(id, session.get("user_id"))
        flash("Compliance alert marked as Resolved.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("compliance.compliance_dashboard"))
