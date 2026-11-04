import os
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request

from backend.ai.pipeline import evaluate_multiple_onion_images
from backend.ai.preprocessor import ImageQualityError
from backend.database.db import db
from backend.models.evaluation import Evaluation, EvaluationImage, EvaluationItem
from backend.models.farmer import FarmerProfile
from backend.models.officer import OfficerFarmer, OfficerProfile
from backend.models.report import Report
from backend.models.user import User
from backend.services.market_price_service import MarketPriceService
from backend.services.pdf_service import generate_evaluation_pdf
from backend.services.price_engine import PriceEngine
from backend.utils.auth_helpers import (
    generate_farmer_id,
    generate_report_id,
    get_current_user,
    login_required,
    role_required,
)
from backend.utils.file_helpers import allowed_file, save_upload_file
from config import Config

officer_bp = Blueprint("officer_bp", __name__, url_prefix="/api/officer")

@officer_bp.route("/dashboard", methods=["GET"])
@login_required
@role_required("officer")
def get_dashboard():
    user = get_current_user()
    officer = user.officer_profile
    if not officer:
        return jsonify({"success": False, "error": "Officer profile not found."}), 404

    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

    all_evals = Evaluation.query.filter_by(status="confirmed").all()
    today_evals = [e for e in all_evals if e.evaluation_date and e.evaluation_date.replace(tzinfo=timezone.utc) >= today_start]

    total_farmers = OfficerFarmer.query.filter_by(officer_id=officer.id).count()
    total_onions = sum(e.total_onions for e in all_evals)
    total_grade_a = sum(e.grade_a_count for e in all_evals)
    total_urs = sum(e.urs_count for e in all_evals)
    total_rejected = sum(e.rejected_count for e in all_evals)

    # Today's counts
    today_onions = sum(e.total_onions for e in today_evals)
    today_grade_a = sum(e.grade_a_count for e in today_evals)
    today_urs = sum(e.urs_count for e in today_evals)
    today_rejected = sum(e.rejected_count for e in today_evals)

    recent_evals = Evaluation.query.filter_by(status="confirmed")\
        .order_by(Evaluation.evaluation_date.desc()).limit(8).all()

    # Mandi prices
    market_prices = MarketPriceService.get_market_prices()[:4]

    # Weekly trend
    trend_labels = []
    trend_counts = []
    trend_grade_a = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_label = day.strftime("%d %b")
        trend_labels.append(day_label)
        day_evals = [e for e in all_evals if e.evaluation_date and e.evaluation_date.strftime("%d %b") == day_label]
        trend_counts.append(len(day_evals))
        trend_grade_a.append(sum(e.grade_a_count for e in day_evals))

    return jsonify({
        "success": True,
        "officer": officer.to_dict(),
        "stats": {
            "today_evaluations": len(today_evals),
            "today_onions": today_onions,
            "today_grade_a": today_grade_a,
            "today_urs": today_urs,
            "today_rejected": today_rejected,
            "total_farmers": total_farmers,
            "total_evaluations": len(all_evals),
            "total_onions": total_onions,
            "grade_a_count": total_grade_a,
            "urs_count": total_urs,
            "rejected_count": total_rejected,
            "grade_a_pct": round((total_grade_a / total_onions * 100) if total_onions else 0, 1),
            "urs_pct": round((total_urs / total_onions * 100) if total_onions else 0, 1),
            "rejected_pct": round((total_rejected / total_onions * 100) if total_onions else 0, 1)
        },
        "trends": {
            "labels": trend_labels,
            "evaluations": trend_counts,
            "grade_a": trend_grade_a
        },
        "recent_evaluations": [e.to_dict() for e in recent_evals],
        "market_prices": market_prices
    }), 200


@officer_bp.route("/farmers", methods=["GET"])
@login_required
@role_required("officer")
def get_farmers():
    """
    Returns only the farmers in THIS officer's 'My Farmers' list.
    Supports optional query filter (name, phone, farmer_id, village, taluka, district).
    """
    user = get_current_user()
    officer = user.officer_profile
    if not officer:
        return jsonify({"success": False, "error": "Officer profile not found."}), 404

    query = request.args.get("query", "").strip()

    # Query OfficerFarmer joined with FarmerProfile and User for this officer
    q = OfficerFarmer.query.filter_by(officer_id=officer.id).join(FarmerProfile).join(User)
    if query:
        q = q.filter(
            (FarmerProfile.farmer_id.ilike(f"%{query}%")) |
            (User.name.ilike(f"%{query}%")) |
            (User.phone.ilike(f"%{query}%")) |
            (FarmerProfile.village.ilike(f"%{query}%")) |
            (FarmerProfile.district.ilike(f"%{query}%"))
        )

    links = q.order_by(OfficerFarmer.created_at.desc(), User.name.asc()).all()
    return jsonify({
        "success": True,
        "count": len(links),
        "farmers": [link.to_dict() for link in links]
    }), 200


@officer_bp.route("/farmers/search", methods=["GET"])
@login_required
@role_required("officer")
def search_farmer_registry():
    """
    Officer searches an existing farmer from the central Farmer Registry
    using Farmer ID OR Mobile Number.
    If found, displays the registered farmer details.
    If not found:
    "Farmer not found. Please ask the farmer to register through the Farmer Portal."
    """
    user = get_current_user()
    officer = user.officer_profile
    if not officer:
        return jsonify({"success": False, "error": "Officer profile required."}), 403

    query = (request.args.get("query") or request.args.get("search") or request.args.get("identifier") or "").strip()
    if not query:
        return jsonify({"success": False, "error": "Please provide a Farmer ID or Mobile Number."}), 400

    # Search central registry by Farmer ID (exact or partial) OR Mobile Number
    farmer = FarmerProfile.query.filter(
        (FarmerProfile.farmer_id.ilike(query)) |
        (FarmerProfile.farmer_id.ilike(f"FMR-{query}"))
    ).first()

    if not farmer:
        farmer = FarmerProfile.query.join(User).filter(User.phone == query).first()

    if not farmer and query.isdigit():
        farmer = FarmerProfile.query.filter_by(id=int(query)).first()
        if not farmer:
            farmer = FarmerProfile.query.join(User).filter(User.phone.ilike(f"%{query}%")).first()

    if not farmer:
        return jsonify({
            "success": False,
            "error": "Farmer not found. Please ask the farmer to register through the Farmer Portal."
        }), 404

    # Check if this farmer is already added to this officer's list
    is_in_my_list = OfficerFarmer.query.filter_by(
        officer_id=officer.id,
        farmer_id=farmer.id
    ).first() is not None

    return jsonify({
        "success": True,
        "farmer": farmer.to_dict(),
        "is_in_my_list": is_in_my_list
    }), 200


@officer_bp.route("/farmers/add", methods=["POST"])
@login_required
@role_required("officer")
def add_to_my_farmers():
    """
    Officer clicks 'Add to My Farmers'.
    The farmer is then added ONLY to that officer's farmer list.
    The same farmer can be added to multiple approved officers.
    """
    user = get_current_user()
    officer = user.officer_profile
    if not officer:
        return jsonify({"success": False, "error": "Officer profile required."}), 403

    data = request.get_json() or {}
    identifier = str(data.get("farmer_id") or data.get("farmer_profile_id") or "").strip()

    if not identifier:
        return jsonify({"success": False, "error": "Farmer identifier is required."}), 400

    # Search central registry
    farmer = FarmerProfile.query.filter(
        (FarmerProfile.farmer_id.ilike(identifier)) |
        (FarmerProfile.farmer_id.ilike(f"FMR-{identifier}"))
    ).first()

    if not farmer and identifier.isdigit():
        farmer = FarmerProfile.query.filter_by(id=int(identifier)).first()
        if not farmer:
            farmer = FarmerProfile.query.join(User).filter(User.phone == identifier).first()

    if not farmer:
        return jsonify({
            "success": False,
            "error": "Farmer not found. Please ask the farmer to register through the Farmer Portal."
        }), 404

    existing = OfficerFarmer.query.filter_by(
        officer_id=officer.id,
        farmer_id=farmer.id
    ).first()

    if existing:
        return jsonify({
            "success": True,
            "message": f"Farmer {farmer.user.name if farmer.user else farmer.farmer_id} is already in your My Farmers list.",
            "farmer": farmer.to_dict(),
            "already_added": True
        }), 200

    try:
        new_link = OfficerFarmer(
            officer_id=officer.id,
            farmer_id=farmer.id
        )
        db.session.add(new_link)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Farmer {farmer.user.name if farmer.user else farmer.farmer_id} added to My Farmers successfully.",
            "farmer": farmer.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to add farmer to your list: {e!s}"}), 500


@officer_bp.route("/farmers/remove", methods=["POST"])
@officer_bp.route("/farmers/<int:farmer_profile_id>", methods=["DELETE"])
@login_required
@role_required("officer")
def remove_from_my_farmers(farmer_profile_id=None):
    """
    Officer can Remove the farmer from their list.
    Removing must NOT delete the farmer from the central Farmer Registry.
    """
    user = get_current_user()
    officer = user.officer_profile
    if not officer:
        return jsonify({"success": False, "error": "Officer profile required."}), 403

    if not farmer_profile_id:
        data = request.get_json() or {}
        fid_val = data.get("farmer_profile_id") or data.get("farmer_id")
        if isinstance(fid_val, int) or (isinstance(fid_val, str) and fid_val.isdigit()):
            farmer_profile_id = int(fid_val)
        elif isinstance(fid_val, str) and fid_val.strip():
            f = FarmerProfile.query.filter_by(farmer_id=fid_val.strip()).first()
            if f:
                farmer_profile_id = f.id

    if not farmer_profile_id:
        return jsonify({"success": False, "error": "Farmer ID is required."}), 400

    link = OfficerFarmer.query.filter_by(
        officer_id=officer.id,
        farmer_id=farmer_profile_id
    ).first()

    if not link:
        return jsonify({"success": False, "error": "Farmer is not in your list."}), 404

    try:
        db.session.delete(link)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Farmer removed from your list successfully. The farmer record remains safely in the central Farmer Registry."
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to remove farmer from your list: {e!s}"}), 500


@officer_bp.route("/farmer-lookup", methods=["GET"])
@officer_bp.route("/farmer-lookup/<farmer_identifier>", methods=["GET"])
@login_required
@role_required("officer")
def lookup_farmer(farmer_identifier=None):
    """
    Fetches registered farmer details for evaluation.
    Officer can select/search ONLY farmers from their own 'My Farmers' list.
    If farmer is not found:
    "Farmer not found. Please ask the farmer to register through the Farmer Portal."
    """
    user = get_current_user()
    officer = user.officer_profile
    if not officer:
        return jsonify({"success": False, "error": "Officer profile required."}), 403

    fid = (farmer_identifier or request.args.get("farmer_id") or "").strip()
    if not fid:
        return jsonify({"success": False, "error": "Farmer ID is required."}), 400

    # Search central registry first
    farmer = FarmerProfile.query.filter(
        (FarmerProfile.farmer_id.ilike(fid)) | (FarmerProfile.farmer_id.ilike(f"FMR-{fid}"))
    ).first()

    if not farmer and fid.isdigit():
        farmer = FarmerProfile.query.filter_by(id=int(fid)).first()
        if not farmer:
            farmer = FarmerProfile.query.join(User).filter(User.phone == fid).first()

    if not farmer:
        return jsonify({
            "success": False,
            "error": "Farmer not found. Please ask the farmer to register through the Farmer Portal."
        }), 404

    # Verify the farmer is in THIS officer's My Farmers list
    link = OfficerFarmer.query.filter_by(officer_id=officer.id, farmer_id=farmer.id).first()
    if not link:
        return jsonify({
            "success": False,
            "error": "Farmer not found. Please ask the farmer to register through the Farmer Portal.",
            "not_in_officer_list": True,
            "tip": "Farmer is in the central registry but not in your My Farmers list. Please add them from Manage Farmers first."
        }), 404

    return jsonify({
        "success": True,
        "message": f"Farmer details retrieved successfully for {farmer.user.name if farmer.user else ''}",
        "farmer": farmer.to_dict()
    }), 200


@officer_bp.route("/farmers", methods=["POST"])
@login_required
@role_required("officer")
def create_farmer():
    """Farmer registration is NOT allowed through the Officer Portal."""
    return jsonify({
        "success": False,
        "error": "Farmer registration must happen ONLY through the Farmer Portal. Officer registration is disabled."
    }), 403


@officer_bp.route("/evaluate", methods=["POST"])
@login_required
@role_required("officer")
def run_evaluation():
    """
    Step 2/3 of Onion Evaluation Workflow:
    Accepts farmer_id and 1 to any number of uploaded image files (different angles/samples).
    Validates farmer is in officer's My Farmers list.
    Runs YOLO detection and Keras classification across all images.
    Returns aggregated AI results for Officer review.
    """
    officer_user = get_current_user()
    officer = officer_user.officer_profile
    if not officer:
        return jsonify({"success": False, "error": "Officer profile required."}), 403

    farmer_id_str = request.form.get("farmer_id", "").strip()
    if not farmer_id_str:
        return jsonify({"success": False, "error": "Please select a farmer."}), 400

    # Look up farmer profile
    farmer = FarmerProfile.query.filter_by(farmer_id=farmer_id_str).first()
    if not farmer and farmer_id_str.isdigit():
        farmer = db.session.get(FarmerProfile, int(farmer_id_str))

    if not farmer:
        return jsonify({"success": False, "error": "Farmer not found. Please ask the farmer to register through the Farmer Portal."}), 404

    # Verify farmer belongs to this officer's My Farmers list
    link = OfficerFarmer.query.filter_by(officer_id=officer.id, farmer_id=farmer.id).first()
    if not link:
        return jsonify({
            "success": False,
            "error": "Selected farmer is not in your My Farmers list. Please add them from Manage Farmers first."
        }), 400

    # Collect all uploaded image files (accepts multiple under 'images' or 'image')
    uploaded_files = []
    if "images" in request.files:
        uploaded_files.extend([f for f in request.files.getlist("images") if f and f.filename])
    if "image" in request.files:
        uploaded_files.extend([f for f in request.files.getlist("image") if f and f.filename])

    if not uploaded_files:
        return jsonify({"success": False, "error": "Please upload at least one onion image."}), 400

    # Validate each image file format
    for file in uploaded_files:
        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "error": f"Invalid format in '{file.filename}'. Only JPG, JPEG, PNG and WEBP are supported."
            }), 400

    # Save all uploaded images
    saved_paths = []
    try:
        for file in uploaded_files:
            _, original_path = save_upload_file(file, Config.UPLOAD_FOLDER)
            saved_paths.append(original_path)
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to save uploaded image(s): {e!s}"}), 500

    # Run AI Pipeline across all images
    try:
        results = evaluate_multiple_onion_images(saved_paths)
    except ImageQualityError as eq:
        return jsonify({
            "success": False,
            "error": eq.message,
            "code": eq.error_code
        }), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"AI evaluation could not be completed: {e!s}"}), 500

    # Fetch Lasalgaon Mandi Reference & Compute Price Estimation
    mandi_ref = PriceEngine.get_lasalgaon_reference_price()
    modal_price = mandi_ref.get("modal_price") if mandi_ref.get("available") else None
    price_est = PriceEngine.calculate_price_estimation(
        grade_a_pct=results["grades"]["Grade A"]["percentage"],
        urs_pct=results["grades"]["URS"]["percentage"],
        rejected_pct=results["grades"]["Rejected"]["percentage"],
        modal_price=modal_price,
        quantity_quintals=0.0
    )

    # Create draft evaluation record with aggregated metrics
    try:
        evaluation = Evaluation(
            farmer_id=farmer.id,
            officer_id=officer.id,
            original_image_path=results["primary_original_image_path"],
            annotated_image_path=results["primary_annotated_image_path"],
            total_images=results["total_images"],
            total_onions=results["total_onions"],
            healthy_count=results["classes"]["Healthy"]["count"],
            damaged_count=results["classes"]["Damaged"]["count"],
            rotten_count=results["classes"]["Rotten"]["count"],
            sprouted_count=results["classes"]["Sprouted"]["count"],
            uncertain_count=results["classes"]["Uncertain"]["count"],
            grade_a_count=results["grades"]["Grade A"]["count"],
            urs_count=results["grades"]["URS"]["count"],
            rejected_count=results["grades"]["Rejected"]["count"],
            overall_result=results["overall_result"],
            quality_summary=results["quality_summary"],
            mandi_name=mandi_ref.get("market_name", "Lasalgaon APMC Mandi"),
            mandi_modal_price=modal_price,
            mandi_price_date=mandi_ref.get("price_date"),
            mandi_api_source=mandi_ref.get("source", "data.gov.in"),
            quality_score=price_est.get("quality_score_pct"),
            estimated_price_per_quintal=price_est.get("estimated_price_per_quintal"),
            quantity_quintals=0.0,
            total_payout=0.0,
            evaluation_date=datetime.now(timezone.utc),
            status="pending_confirmation"
        )
        db.session.add(evaluation)
        db.session.flush()

        # Save individual images breakdown
        for img_res in results["per_image_results"]:
            eval_img = EvaluationImage(
                evaluation_id=evaluation.id,
                image_order=img_res["image_order"],
                original_image_path=img_res["original_image_path"],
                annotated_image_path=img_res["annotated_image_path"],
                total_onions=img_res["total_onions"],
                healthy_count=img_res["classes"]["Healthy"]["count"],
                damaged_count=img_res["classes"]["Damaged"]["count"],
                rotten_count=img_res["classes"]["Rotten"]["count"],
                sprouted_count=img_res["classes"]["Sprouted"]["count"],
                uncertain_count=img_res["classes"]["Uncertain"]["count"]
            )
            db.session.add(eval_img)

        # Save individual item detections across all images
        for item in results["detections"]:
            eval_item = EvaluationItem(
                evaluation_id=evaluation.id,
                image_order=item.get("image_order", 1),
                onion_number=item["onion_number"],
                class_name=item["class_name"],
                classification_confidence=item["classification_confidence"],
                detection_confidence=item["detection_confidence"],
                x1=item["bounding_box"][0],
                y1=item["bounding_box"][1],
                x2=item["bounding_box"][2],
                y2=item["bounding_box"][3]
            )
            db.session.add(eval_item)

        db.session.commit()

        annotated_url = f"/outputs/{os.path.basename(results['primary_annotated_image_path'])}"

        return jsonify({
            "success": True,
            "evaluation_id": evaluation.id,
            "farmer": farmer.to_dict(),
            "price_estimation": {
                **price_est,
                "mandi_info": {
                    "available": mandi_ref.get("available", False),
                    "market_name": mandi_ref.get("market_name", "Lasalgaon APMC Mandi"),
                    "district": mandi_ref.get("district", "Nashik"),
                    "state": mandi_ref.get("state", "Maharashtra"),
                    "price_date": mandi_ref.get("price_date"),
                    "source": mandi_ref.get("source", "data.gov.in"),
                    "status": mandi_ref.get("status", "unknown"),
                    "is_live": mandi_ref.get("is_live", False),
                    "note": mandi_ref.get("note", ""),
                    "error": mandi_ref.get("error", "")
                }
            },
            "results": {
                "total_images": results["total_images"],
                "total_onions": results["total_onions"],
                "classes": results["classes"],
                "grades": results["grades"],
                "overall_result": results["overall_result"],
                "quality_summary": results["quality_summary"],
                "is_overlapping": results.get("is_overlapping", False),
                "overlapping_pairs": results.get("overlapping_pairs", 0),
                "advisory_notes": results.get("advisory_notes"),
                "annotated_image_url": annotated_url,
                "images": [
                    {
                        "image_order": img["image_order"],
                        "original_filename": img["original_filename"],
                        "annotated_url": img["annotated_url"],
                        "total_onions": img["total_onions"],
                        "classes": img["classes"],
                        "grades": img["grades"]
                    }
                    for img in results["per_image_results"]
                ],
                "detections": results["detections"]
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to record evaluation: {e!s}"}), 500


@officer_bp.route("/evaluate/<int:eval_id>/confirm", methods=["POST"])
@login_required
@role_required("officer")
def confirm_evaluation(eval_id):
    """
    Officer reviews and confirms the AI evaluation:
    1. Assigns permanent Report ID (e.g. ONR-2026-000124)
    2. Updates status to 'confirmed'
    3. Generates official PDF report
    4. Records Report in database
    """
    evaluation = db.session.get(Evaluation, eval_id)
    if not evaluation:
        return jsonify({"success": False, "error": "Evaluation not found."}), 404

    if evaluation.status == "confirmed" and evaluation.report_id:
        return jsonify({
            "success": True,
            "message": "Evaluation already confirmed.",
            "report_id": evaluation.report_id,
            "pdf_url": f"/reports/download/Onion_Report_{evaluation.report_id}.pdf"
        }), 200

    payload = request.get_json(silent=True) or request.form or {}
    quantity_input = payload.get("quantity_quintals")
    if quantity_input is not None:
        try:
            evaluation.quantity_quintals = max(0.0, float(quantity_input))
        except (ValueError, TypeError):
            pass

    modal_input = payload.get("mandi_modal_price")
    if modal_input is not None:
        try:
            m_val = float(modal_input)
            if m_val > 0:
                evaluation.mandi_modal_price = m_val
        except (ValueError, TypeError):
            pass

    if payload.get("mandi_name"):
        evaluation.mandi_name = str(payload.get("mandi_name")).strip()
    if payload.get("mandi_api_source"):
        evaluation.mandi_api_source = str(payload.get("mandi_api_source")).strip()
    if payload.get("mandi_price_date"):
        evaluation.mandi_price_date = str(payload.get("mandi_price_date")).strip()

    # Process Officer Item Overrides / Human Review
    item_overrides = payload.get("item_overrides")
    if item_overrides and isinstance(item_overrides, list):
        override_map = {}
        for it in item_overrides:
            if isinstance(it, dict) and "onion_number" in it and "class_name" in it:
                try:
                    override_map[int(it["onion_number"])] = str(it["class_name"]).strip()
                except (ValueError, TypeError):
                    pass

        if override_map:
            for item in evaluation.items:
                if item.onion_number in override_map:
                    new_c = override_map[item.onion_number]
                    if new_c in Config.QUALITY_CLASSES:
                        item.class_name = new_c

            # Recalculate evaluation-level counts
            h_count = sum(1 for it in evaluation.items if it.class_name == "Healthy")
            d_count = sum(1 for it in evaluation.items if it.class_name == "Damaged")
            r_count = sum(1 for it in evaluation.items if it.class_name == "Rotten")
            s_count = sum(1 for it in evaluation.items if it.class_name == "Sprouted")

            evaluation.healthy_count = h_count
            evaluation.damaged_count = d_count
            evaluation.rotten_count = r_count
            evaluation.sprouted_count = s_count
            evaluation.uncertain_count = sum(1 for it in evaluation.items if it.class_name not in Config.QUALITY_CLASSES)

            evaluation.grade_a_count = h_count
            evaluation.urs_count = d_count
            evaluation.rejected_count = r_count + s_count

            tot_items = len(evaluation.items) or 1
            ga_rate = round((h_count / tot_items) * 100, 1)
            urs_rate = round((d_count / tot_items) * 100, 1)
            if ga_rate >= 75:
                evaluation.overall_result = "Grade A - Premium Quality"
            elif (ga_rate + urs_rate) >= 70:
                evaluation.overall_result = "URS Standard - Commercial Quality"
            else:
                evaluation.overall_result = "High Rejection - Substandard Batch"

            # Update per-image counts in EvaluationImage
            for eval_img in evaluation.images:
                sub_items = [it for it in evaluation.items if (it.image_order or 1) == eval_img.image_order]
                eval_img.healthy_count = sum(1 for it in sub_items if it.class_name == "Healthy")
                eval_img.damaged_count = sum(1 for it in sub_items if it.class_name == "Damaged")
                eval_img.rotten_count = sum(1 for it in sub_items if it.class_name == "Rotten")
                eval_img.sprouted_count = sum(1 for it in sub_items if it.class_name == "Sprouted")

    # Recalculate price estimation to guarantee data consistency
    total_onions = evaluation.total_onions or 1
    ga_pct = round((evaluation.grade_a_count / total_onions) * 100, 1)
    urs_pct = round((evaluation.urs_count / total_onions) * 100, 1)
    rej_pct = round((evaluation.rejected_count / total_onions) * 100, 1)

    urs_multiplier = payload.get("urs_multiplier")
    if urs_multiplier is None:
        urs_multiplier = payload.get("urs_factor")

    price_calc = PriceEngine.calculate_price_estimation(
        grade_a_pct=ga_pct,
        urs_pct=urs_pct,
        rejected_pct=rej_pct,
        modal_price=evaluation.mandi_modal_price,
        quantity_quintals=evaluation.quantity_quintals,
        urs_multiplier=urs_multiplier
    )
    evaluation.quality_score = price_calc["quality_score_pct"]
    evaluation.estimated_price_per_quintal = price_calc["estimated_price_per_quintal"]
    evaluation.total_payout = price_calc["total_payout"]

    language = str(payload.get("language") or "en").lower().strip()
    if language not in ("en", "hi", "mr"):
        language = "en"
    evaluation.report_language = language

    try:
        report_id = generate_report_id()
        evaluation.report_id = report_id
        evaluation.status = "confirmed"
        evaluation.evaluation_date = datetime.now(timezone.utc)

        # Generate official PDF Report with Price Estimation Table in selected language
        _pdf_fn, pdf_fp, pdf_size = generate_evaluation_pdf(evaluation, language=language)

        report = Report(
            evaluation_id=evaluation.id,
            pdf_path=pdf_fp,
            file_size_bytes=pdf_size,
            language=language
        )
        db.session.add(report)
        db.session.flush()

        # Automatic Digital Procurement Transaction Record & Audit Trail
        from backend.utils.audit_helpers import record_audit_log
        from backend.utils.transaction_helpers import create_transaction_for_evaluation
        create_transaction_for_evaluation(evaluation, commit=False)

        # Automatic Predictive Inventory Sync
        from backend.services.predictive_inventory_service import PredictiveInventoryService
        PredictiveInventoryService.sync_evaluation_to_inventory(evaluation, commit=False)

        record_audit_log(
            action="CONFIRM_EVALUATION",
            entity_type="evaluation",
            entity_id=report_id,
            details={
                "evaluation_id": evaluation.id,
                "officer_id": evaluation.officer.officer_id if evaluation.officer else None,
                "farmer_id": evaluation.farmer.farmer_id if evaluation.farmer else None,
                "language": language,
                "total_onions": evaluation.total_onions,
                "grade_a_count": evaluation.grade_a_count,
                "overall_result": evaluation.overall_result
            }
        )

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Report {report_id} successfully confirmed and published in {language.upper()}!",
            "report_id": report_id,
            "language": language,
            "pdf_url": f"/reports/download/Onion_Report_{report_id}.pdf",
            "evaluation": evaluation.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to confirm report: {e!s}"}), 500


@officer_bp.route("/evaluate/<int:eval_id>/payout", methods=["POST", "PUT"])
@login_required
@role_required("officer")
def update_payout(eval_id):
    """
    Allows officer to enter or update the procured batch quantity and recalculate payout.
    Automatically regenerates the official PDF report with updated payout.
    """
    evaluation = db.session.get(Evaluation, eval_id)
    if not evaluation:
        return jsonify({"success": False, "error": "Evaluation record not found."}), 404

    payload = request.get_json(silent=True) or request.form or {}
    quantity_input = payload.get("quantity_quintals")
    if quantity_input is None:
        return jsonify({"success": False, "error": "Quantity in quintals is required."}), 400

    try:
        qty = max(0.0, float(quantity_input))
        evaluation.quantity_quintals = qty
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid quantity provided."}), 400

    # Optional modal price update
    modal_input = payload.get("mandi_modal_price")
    if modal_input is not None:
        try:
            m_val = float(modal_input)
            if m_val > 0:
                evaluation.mandi_modal_price = m_val
        except (ValueError, TypeError):
            pass

    # Recalculate price estimation
    total_onions = evaluation.total_onions or 1
    ga_pct = round((evaluation.grade_a_count / total_onions) * 100, 1)
    urs_pct = round((evaluation.urs_count / total_onions) * 100, 1)
    rej_pct = round((evaluation.rejected_count / total_onions) * 100, 1)

    price_calc = PriceEngine.calculate_price_estimation(
        grade_a_pct=ga_pct,
        urs_pct=urs_pct,
        rejected_pct=rej_pct,
        modal_price=evaluation.mandi_modal_price,
        quantity_quintals=evaluation.quantity_quintals
    )
    evaluation.quality_score = price_calc["quality_score_pct"]
    evaluation.estimated_price_per_quintal = price_calc["estimated_price_per_quintal"]
    evaluation.total_payout = price_calc["total_payout"]

    try:
        # Regenerate PDF report if report exists
        if evaluation.status == "confirmed" and evaluation.report_id:
            rep_lang = evaluation.report_language or (evaluation.report.language if evaluation.report else "en")
            _pdf_fn, pdf_fp, pdf_size = generate_evaluation_pdf(evaluation, language=rep_lang)
            if evaluation.report:
                evaluation.report.pdf_path = pdf_fp
                evaluation.report.file_size_bytes = pdf_size
        # Sync updated physical quantity to Inventory
        from backend.services.predictive_inventory_service import PredictiveInventoryService
        PredictiveInventoryService.sync_evaluation_to_inventory(evaluation, commit=False)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Batch quantity and payout updated successfully.",
            "evaluation": evaluation.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to update payout: {e!s}"}), 500



@officer_bp.route("/reports", methods=["GET"])
@login_required
@role_required("officer")
def get_reports():
    search = request.args.get("search", "").strip()
    grade = request.args.get("grade", "").strip()
    lang = request.args.get("language", "").strip() or request.args.get("lang", "").strip()

    query = Evaluation.query.filter_by(status="confirmed")

    if search:
        query = query.join(FarmerProfile).join(User).filter(
            (Evaluation.report_id.ilike(f"%{search}%")) |
            (FarmerProfile.farmer_id.ilike(f"%{search}%")) |
            (User.name.ilike(f"%{search}%"))
        )

    if lang:
        query = query.filter(Evaluation.report_language == lang)

    if grade:
        if grade == "Grade A":
            query = query.filter(Evaluation.overall_result.ilike("%Grade A%"))
        elif grade == "URS":
            query = query.filter(Evaluation.overall_result.ilike("%URS%"))
        elif grade == "Rejected":
            query = query.filter(Evaluation.overall_result.ilike("%Rejection%"))

    evals = query.order_by(Evaluation.evaluation_date.desc()).all()
    return jsonify({
        "success": True,
        "total": len(evals),
        "reports": [e.to_dict() for e in evals]
    }), 200


# =========================================================================
# PREDICTIVE INVENTORY & DECISION SUPPORT APIS
# =========================================================================
@officer_bp.route("/predictive-inventory", methods=["GET"])
@login_required
@role_required("officer")
def get_predictive_inventory():
    """
    Returns center-level predictive inventory, storage-life analysis,
    demand forecasts (7d, 14d, 30d), and AI-assisted Sell/Store recommendations.
    """
    user = get_current_user()
    officer = user.officer_profile
    if not officer:
        return jsonify({"success": False, "error": "Officer profile not found."}), 404

    center_filter = request.args.get("center", "").strip() or None
    from backend.services.predictive_inventory_service import PredictiveInventoryService
    data = PredictiveInventoryService.get_officer_inventory(officer.id, center_filter=center_filter)
    return jsonify(data), 200


@officer_bp.route("/inventory/update-quantity", methods=["POST"])
@login_required
@role_required("officer")
def update_inventory_batch_quantity():
    """
    Allows procurement officer to enter or update verified physical quantity
    for an inventory batch (in kg, quintals, or tonnes).
    Never guesses or invents quantities.
    """
    user = get_current_user()
    officer = user.officer_profile
    if not officer:
        return jsonify({"success": False, "error": "Officer profile not found."}), 404

    payload = request.get_json(silent=True) or {}
    batch_id = payload.get("batch_id")
    quantity = payload.get("quantity")
    unit = payload.get("unit", "kg")

    if not batch_id or quantity is None:
        return jsonify({"success": False, "error": "Batch ID and quantity are required."}), 400

    from backend.services.predictive_inventory_service import PredictiveInventoryService
    res = PredictiveInventoryService.update_batch_quantity(batch_id, quantity, unit)
    status_code = 200 if res.get("success") else 400
    return jsonify(res), status_code


@officer_bp.route("/inventory/dispatch", methods=["POST"])
@login_required
@role_required("officer")
def record_inventory_dispatch():
    """
    Records an outbound sale or dispatch of onions from an inventory batch.
    Strictly prevents negative inventory.
    """
    user = get_current_user()
    officer = user.officer_profile
    if not officer:
        return jsonify({"success": False, "error": "Officer profile not found."}), 404

    payload = request.get_json(silent=True) or {}
    batch_id = payload.get("batch_id")
    quantity_kg = payload.get("quantity_kg")
    reason = payload.get("reason", "Outbound sale/dispatch")
    destination = payload.get("destination", "Local Market / Trader")

    if not batch_id or quantity_kg is None:
        return jsonify({"success": False, "error": "Batch ID and quantity_kg are required."}), 400

    from backend.services.predictive_inventory_service import PredictiveInventoryService
    res = PredictiveInventoryService.record_dispatch(batch_id, quantity_kg, reason, destination)
    status_code = 200 if res.get("success") else 400
    return jsonify(res), status_code
