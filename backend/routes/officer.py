import os
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request

from backend.ai.pipeline import evaluate_multiple_onion_images
from backend.database.db import db
from backend.models.evaluation import Evaluation, EvaluationImage, EvaluationItem
from backend.models.farmer import FarmerProfile
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

    total_farmers = FarmerProfile.query.count()
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
    query = request.args.get("query", "").strip()
    farmer_query = FarmerProfile.query.join(User)

    if query:
        farmer_query = farmer_query.filter(
            (FarmerProfile.farmer_id.ilike(f"%{query}%")) |
            (User.name.ilike(f"%{query}%")) |
            (User.phone.ilike(f"%{query}%")) |
            (FarmerProfile.village.ilike(f"%{query}%")) |
            (FarmerProfile.district.ilike(f"%{query}%"))
        )

    farmers = farmer_query.order_by(User.name).all()
    return jsonify({
        "success": True,
        "farmers": [f.to_dict() for f in farmers]
    }), 200


@officer_bp.route("/farmers", methods=["POST"])
@login_required
@role_required("officer")
def create_farmer():
    """Allows an officer to quickly register a new farmer during procurement."""
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip() or None
    village = data.get("village", "").strip()
    taluka = data.get("taluka", "").strip()
    district = data.get("district", "").strip()
    state = data.get("state", "Maharashtra").strip()
    default_pw = data.get("password", "farmer123")

    if not name or not phone or len(phone) < 10 or not village or not taluka or not district:
        return jsonify({"success": False, "error": "Name, 10-digit mobile, village, taluka and district are required."}), 400

    if User.query.filter_by(phone=phone).first():
        return jsonify({"success": False, "error": "Farmer with this mobile number already exists."}), 400

    try:
        user = User(name=name, phone=phone, email=email, role="farmer")
        user.set_password(default_pw)
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

        return jsonify({
            "success": True,
            "message": f"Farmer {name} registered with ID: {farmer_id}",
            "farmer": farmer_profile.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to add farmer: {e!s}"}), 500


@officer_bp.route("/evaluate", methods=["POST"])
@login_required
@role_required("officer")
def run_evaluation():
    """
    Step 2/3 of Onion Evaluation Workflow:
    Accepts farmer_id and 1 to any number of uploaded image files (different angles/samples).
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
        return jsonify({"success": False, "error": f"Farmer '{farmer_id_str}' not found."}), 404

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

    try:
        report_id = generate_report_id()
        evaluation.report_id = report_id
        evaluation.status = "confirmed"
        evaluation.evaluation_date = datetime.now(timezone.utc)

        # Generate official PDF Report with Price Estimation Table
        _pdf_fn, pdf_fp, pdf_size = generate_evaluation_pdf(evaluation)

        report = Report(
            evaluation_id=evaluation.id,
            pdf_path=pdf_fp,
            file_size_bytes=pdf_size
        )
        db.session.add(report)
        db.session.flush()

        # Automatic Digital Procurement Transaction Record & Audit Trail
        from backend.utils.audit_helpers import record_audit_log
        from backend.utils.transaction_helpers import create_transaction_for_evaluation
        create_transaction_for_evaluation(evaluation, commit=False)

        record_audit_log(
            action="CONFIRM_EVALUATION",
            entity_type="evaluation",
            entity_id=report_id,
            details={
                "evaluation_id": evaluation.id,
                "officer_id": evaluation.officer.officer_id if evaluation.officer else None,
                "farmer_id": evaluation.farmer.farmer_id if evaluation.farmer else None,
                "total_onions": evaluation.total_onions,
                "grade_a_count": evaluation.grade_a_count,
                "overall_result": evaluation.overall_result
            }
        )

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Report {report_id} successfully confirmed and published!",
            "report_id": report_id,
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
            _pdf_fn, pdf_fp, pdf_size = generate_evaluation_pdf(evaluation)
            if evaluation.report:
                evaluation.report.pdf_path = pdf_fp
                evaluation.report.file_size_bytes = pdf_size

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

    query = Evaluation.query.filter_by(status="confirmed")

    if search:
        query = query.join(FarmerProfile).join(User).filter(
            (Evaluation.report_id.ilike(f"%{search}%")) |
            (FarmerProfile.farmer_id.ilike(f"%{search}%")) |
            (User.name.ilike(f"%{search}%"))
        )

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
