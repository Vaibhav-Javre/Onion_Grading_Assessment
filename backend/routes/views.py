from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    send_from_directory,
    session,
    url_for,
)

from backend.models.evaluation import Evaluation
from backend.utils.auth_helpers import get_current_user, login_required, role_required
from config import Config

views_bp = Blueprint("views", __name__)

@views_bp.route("/")
def home():
    if "user_id" in session:
        role = session.get("user_role")
        if role == "farmer":
            return redirect(url_for("views.farmer_dashboard"))
        elif role == "officer":
            return redirect(url_for("views.officer_dashboard"))
        elif role in ("government", "admin"):
            return redirect(url_for("views.government_dashboard"))
    return render_template("index.html")

# Auth views
@views_bp.route("/login/farmer")
def login_farmer():
    if "user_id" in session and session.get("user_role") == "farmer":
        return redirect(url_for("views.farmer_dashboard"))
    return render_template("auth/login_farmer.html")

@views_bp.route("/register/farmer")
def register_farmer():
    if "user_id" in session and session.get("user_role") == "farmer":
        return redirect(url_for("views.farmer_dashboard"))
    return render_template("auth/register_farmer.html")

@views_bp.route("/login/officer")
def login_officer():
    if "user_id" in session and session.get("user_role") == "officer":
        return redirect(url_for("views.officer_dashboard"))
    return render_template("auth/login_officer.html")

@views_bp.route("/login/government")
@views_bp.route("/login/admin")
def login_government():
    if "user_id" in session and session.get("user_role") in ("government", "admin"):
        return redirect(url_for("views.government_dashboard"))
    return render_template("auth/login_government.html")

@views_bp.route("/logout")
def logout_view():
    session.clear()
    return redirect(url_for("views.home"))

# Farmer views
@views_bp.route("/farmer/dashboard")
@login_required
@role_required("farmer")
def farmer_dashboard():
    user = get_current_user()
    return render_template("farmer/dashboard.html", user=user, farmer=user.farmer_profile)

@views_bp.route("/farmer/reports")
@login_required
@role_required("farmer")
def farmer_reports():
    user = get_current_user()
    return render_template("farmer/reports.html", user=user, farmer=user.farmer_profile)

@views_bp.route("/farmer/report/<report_identifier>")
@login_required
@role_required("farmer")
def farmer_report_detail(report_identifier):
    user = get_current_user()
    farmer = user.farmer_profile
    
    eval_record = None
    if report_identifier.isdigit():
        eval_record = Evaluation.query.filter_by(id=int(report_identifier)).first()
    if not eval_record:
        eval_record = Evaluation.query.filter_by(report_id=report_identifier).first()

    if not eval_record:
        flash("Report not found.", "danger")
        return redirect(url_for("views.farmer_reports"))

    # Strictly check ownership!
    if eval_record.farmer_id != farmer.id:
        flash("Unauthorized: You can only view your own assessment reports.", "danger")
        return redirect(url_for("views.farmer_reports"))

    return render_template("farmer/report_detail.html", user=user, farmer=farmer, evaluation=eval_record)

@views_bp.route("/farmer/market")
@login_required
@role_required("farmer")
def farmer_market():
    user = get_current_user()
    return render_template("farmer/market.html", user=user, farmer=user.farmer_profile)

@views_bp.route("/farmer/profile")
@login_required
@role_required("farmer")
def farmer_profile():
    user = get_current_user()
    return render_template("farmer/profile.html", user=user, farmer=user.farmer_profile)

# Officer views
@views_bp.route("/officer/dashboard")
@login_required
@role_required("officer")
def officer_dashboard():
    user = get_current_user()
    return render_template("officer/dashboard.html", user=user, officer=user.officer_profile)

@views_bp.route("/officer/evaluate")
@login_required
@role_required("officer")
def officer_evaluate():
    user = get_current_user()
    return render_template("officer/evaluate.html", user=user, officer=user.officer_profile)

@views_bp.route("/officer/farmers")
@login_required
@role_required("officer")
def officer_farmers():
    user = get_current_user()
    return render_template("officer/farmers.html", user=user, officer=user.officer_profile)

@views_bp.route("/officer/reports")
@login_required
@role_required("officer")
def officer_reports():
    user = get_current_user()
    return render_template("officer/reports.html", user=user, officer=user.officer_profile)

@views_bp.route("/officer/report/<report_identifier>")
@login_required
@role_required("officer")
def officer_report_detail(report_identifier):
    user = get_current_user()
    officer = user.officer_profile
    
    eval_record = None
    if report_identifier.isdigit():
        eval_record = Evaluation.query.filter_by(id=int(report_identifier)).first()
    if not eval_record:
        eval_record = Evaluation.query.filter_by(report_id=report_identifier).first()

    if not eval_record:
        flash("Report not found.", "danger")
        return redirect(url_for("views.officer_reports"))

    return render_template("officer/report_detail.html", user=user, officer=officer, evaluation=eval_record)

@views_bp.route("/officer/market")
@login_required
@role_required("officer")
def officer_market():
    user = get_current_user()
    return render_template("officer/market.html", user=user, officer=user.officer_profile)

@views_bp.route("/officer/profile")
@login_required
@role_required("officer")
def officer_profile():
    user = get_current_user()
    return render_template("officer/profile.html", user=user, officer=user.officer_profile)

# =========================================================
# Government Portal Views
# =========================================================
@views_bp.route("/government/dashboard")
@login_required
@role_required("government", "admin")
def government_dashboard():
    user = get_current_user()
    return render_template("government/dashboard.html", user=user)

@views_bp.route("/government/farmers")
@login_required
@role_required("government", "admin")
def government_farmers():
    user = get_current_user()
    return render_template("government/farmers.html", user=user)

@views_bp.route("/government/officers")
@login_required
@role_required("government", "admin")
def government_officers():
    user = get_current_user()
    return render_template("government/officers.html", user=user)

@views_bp.route("/government/transactions")
@login_required
@role_required("government", "admin")
def government_transactions():
    user = get_current_user()
    return render_template("government/transactions.html", user=user)

@views_bp.route("/government/reports")
@login_required
@role_required("government", "admin")
def government_reports():
    user = get_current_user()
    return render_template("government/reports.html", user=user)

@views_bp.route("/government/audit-logs")
@login_required
@role_required("government", "admin")
def government_audit_logs():
    user = get_current_user()
    return render_template("government/audit_logs.html", user=user)

@views_bp.route("/government/analytics")
@login_required
@role_required("government", "admin")
def government_analytics():
    user = get_current_user()
    return render_template("government/analytics.html", user=user)

@views_bp.route("/government/search")
@login_required
@role_required("government", "admin")
def government_search():
    user = get_current_user()
    return render_template("government/search.html", user=user)

# Media file serving
@views_bp.route("/outputs/<path:filename>")
def output_file(filename):
    return send_from_directory(Config.OUTPUT_FOLDER, filename)

@views_bp.route("/uploads/<path:filename>")
def upload_file(filename):
    return send_from_directory(Config.UPLOAD_FOLDER, filename)
