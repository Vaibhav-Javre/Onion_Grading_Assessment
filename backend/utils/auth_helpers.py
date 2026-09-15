import random
from datetime import datetime, timezone
from functools import wraps

from flask import flash, jsonify, redirect, request, session, url_for

from backend.database.db import db
from backend.models.user import User


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "Authentication required. Please log in."}), 401
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("views.home"))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                if request.is_json or request.path.startswith("/api/"):
                    return jsonify({"success": False, "error": "Authentication required."}), 401
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("views.home"))

            current_role = session.get("user_role")
            if current_role not in allowed_roles:
                if request.is_json or request.path.startswith("/api/"):
                    return jsonify({"success": False, "error": "Unauthorized access. Insufficient permissions."}), 403
                flash("You do not have permission to access that page.", "danger")
                if current_role == "farmer":
                    return redirect(url_for("views.farmer_dashboard"))
                elif current_role == "officer":
                    return redirect(url_for("views.officer_dashboard"))
                elif current_role in ("government", "admin"):
                    return redirect(url_for("views.government_dashboard"))
                return redirect(url_for("views.home"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def generate_farmer_id():
    """Generates unique ID like FMR-2026-0001"""
    year = datetime.now(timezone.utc).year
    from backend.models.farmer import FarmerProfile
    count = db.session.query(FarmerProfile).count() + 1
    # Check uniqueness
    while True:
        candidate = f"FMR-{year}-{count:04d}"
        if not FarmerProfile.query.filter_by(farmer_id=candidate).first():
            return candidate
        count += 1

def generate_officer_id():
    """Generates unique ID like OFF-2026-001"""
    year = datetime.now(timezone.utc).year
    from backend.models.officer import OfficerProfile
    count = db.session.query(OfficerProfile).count() + 1
    while True:
        candidate = f"OFF-{year}-{count:03d}"
        if not OfficerProfile.query.filter_by(officer_id=candidate).first():
            return candidate
        count += 1

def generate_report_id():
    """Generates unique ID like ONR-2026-000124"""
    year = datetime.now(timezone.utc).year
    from backend.models.evaluation import Evaluation
    count = db.session.query(Evaluation).count() + 1
    # Add a pseudo-random 3-digit salt or sequential
    suffix = random.randint(100, 999)
    while True:
        candidate = f"ONR-{year}-{count:03d}{suffix:03d}"
        if not Evaluation.query.filter_by(report_id=candidate).first():
            return candidate
        count += 1
