from flask import Blueprint, request, jsonify, session, redirect, url_for
from backend.database.db import db
from backend.models.user import User
from backend.models.farmer import FarmerProfile
from backend.models.officer import OfficerProfile
from backend.utils.auth_helpers import generate_farmer_id, get_current_user

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/api/auth")

@auth_bp.route("/register/farmer", methods=["POST"])
def register_farmer():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip() or None
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")
    village = data.get("village", "").strip()
    taluka = data.get("taluka", "").strip()
    district = data.get("district", "").strip()
    state = data.get("state", "Maharashtra").strip()

    # Validation
    if not name:
        return jsonify({"success": False, "error": "Farmer full name is required."}), 400
    if not phone or len(phone) < 10:
        return jsonify({"success": False, "error": "Valid 10-digit mobile number is required."}), 400
    if not password or len(password) < 6:
        return jsonify({"success": False, "error": "Password must be at least 6 characters."}), 400
    if password != confirm_password:
        return jsonify({"success": False, "error": "Passwords do not match."}), 400
    if not village or not taluka or not district:
        return jsonify({"success": False, "error": "Village, Taluka and District are required."}), 400

    # Check duplicates
    if User.query.filter_by(phone=phone).first():
        return jsonify({"success": False, "error": "An account with this mobile number already exists."}), 400
    if email and User.query.filter_by(email=email).first():
        return jsonify({"success": False, "error": "An account with this email already exists."}), 400

    try:
        user = User(
            name=name,
            phone=phone,
            email=email,
            role="farmer"
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        farmer_id = generate_farmer_id()
        farmer_profile = FarmerProfile(
            user_id=user.id,
            farmer_id=farmer_id,
            village=village,
            taluka=taluka,
            district=district,
            state=state
        )
        db.session.add(farmer_profile)
        db.session.commit()

        # Set session
        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_role"] = "farmer"
        session["profile_id"] = farmer_profile.id
        session["farmer_id"] = farmer_id

        return jsonify({
            "success": True,
            "message": f"Registration successful! Your Farmer ID is {farmer_id}",
            "farmer_id": farmer_id,
            "redirect_url": "/farmer/dashboard"
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Registration failed: {str(e)}"}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    identifier = data.get("identifier", "").strip()
    password = data.get("password", "")
    expected_role = data.get("role", "farmer").strip() # 'farmer' or 'officer'

    if not identifier or not password:
        return jsonify({"success": False, "error": "Please provide both identifier and password."}), 400

    user = None
    if expected_role == "farmer":
        # Identifier can be phone, email, or farmer_id
        if identifier.startswith("FMR-"):
            fp = FarmerProfile.query.filter_by(farmer_id=identifier).first()
            if fp:
                user = fp.user
        else:
            user = User.query.filter(
                (User.phone == identifier) | (User.email == identifier)
            ).filter_by(role="farmer").first()

    elif expected_role == "officer":
        # Identifier can be officer_id, phone, or email
        if identifier.startswith("OFF-"):
            op = OfficerProfile.query.filter_by(officer_id=identifier).first()
            if op:
                user = op.user
        else:
            user = User.query.filter(
                (User.email == identifier) | (User.phone == identifier)
            ).filter_by(role="officer").first()

    if not user or not user.check_password(password) or user.role != expected_role:
        return jsonify({"success": False, "error": "Invalid credentials or unauthorized role."}), 401

    # Login successful -> setup session
    session.clear()
    session["user_id"] = user.id
    session["user_name"] = user.name
    session["user_role"] = user.role

    redirect_url = "/farmer/dashboard"
    if user.role == "farmer" and user.farmer_profile:
        session["profile_id"] = user.farmer_profile.id
        session["farmer_id"] = user.farmer_profile.farmer_id
        redirect_url = "/farmer/dashboard"
    elif user.role == "officer" and user.officer_profile:
        session["profile_id"] = user.officer_profile.id
        session["officer_id"] = user.officer_profile.officer_id
        redirect_url = "/officer/dashboard"

    return jsonify({
        "success": True,
        "message": f"Welcome back, {user.name}!",
        "role": user.role,
        "redirect_url": redirect_url
    }), 200


@auth_bp.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    accept_header = request.headers.get("Accept", "")
    is_ajax = request.is_json or (request.headers.get("X-Requested-With") == "XMLHttpRequest") or ("application/json" in accept_header and "text/html" not in accept_header)
    if is_ajax:
        return jsonify({"success": True, "message": "Logged out successfully.", "redirect_url": "/"}), 200
    return redirect("/")


@auth_bp.route("/me", methods=["GET"])
def get_me():
    user = get_current_user()
    if not user:
        return jsonify({"authenticated": False}), 200

    resp = {
        "authenticated": True,
        "id": user.id,
        "name": user.name,
        "role": user.role,
        "phone": user.phone,
        "email": user.email
    }
    if user.role == "farmer" and user.farmer_profile:
        resp["farmer"] = user.farmer_profile.to_dict()
    elif user.role == "officer" and user.officer_profile:
        resp["officer"] = user.officer_profile.to_dict()

    return jsonify(resp), 200


@auth_bp.route("/change-password", methods=["POST"])
def change_password():
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "Authentication required."}), 401

    data = request.get_json() or {}
    old_password = data.get("old_password", "")
    new_password = data.get("new_password", "")

    if not user.check_password(old_password):
        return jsonify({"success": False, "error": "Current password is incorrect."}), 400
    if len(new_password) < 6:
        return jsonify({"success": False, "error": "New password must be at least 6 characters."}), 400

    user.set_password(new_password)
    db.session.commit()
    return jsonify({"success": True, "message": "Password updated successfully."}), 200
