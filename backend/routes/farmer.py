from flask import Blueprint, jsonify, request

from backend.models.evaluation import Evaluation
from backend.services.market_price_service import MarketPriceService
from backend.utils.auth_helpers import get_current_user, login_required, role_required

farmer_bp = Blueprint("farmer_bp", __name__, url_prefix="/api/farmer")

@farmer_bp.route("/dashboard", methods=["GET"])
@login_required
@role_required("farmer")
def get_dashboard():
    user = get_current_user()
    farmer = user.farmer_profile
    if not farmer:
        return jsonify({"success": False, "error": "Farmer profile not found."}), 404

    evaluations = Evaluation.query.filter_by(farmer_id=farmer.id, status="confirmed")\
        .order_by(Evaluation.evaluation_date.desc()).all()

    total_evals = len(evaluations)
    grade_a_total = sum(e.grade_a_count for e in evaluations)
    urs_total = sum(e.urs_count for e in evaluations)
    rejected_total = sum(e.rejected_count for e in evaluations)
    total_onions_all = sum(e.total_onions for e in evaluations)

    latest_eval = evaluations[0].to_dict() if evaluations else None

    # Get local mandi market price for farmer's district
    district_prices = MarketPriceService.get_market_prices(district=farmer.district)
    if not district_prices:
        district_prices = MarketPriceService.get_market_prices() # fallback to primary mandi
    market_price = district_prices[0] if district_prices else None

    return jsonify({
        "success": True,
        "farmer": farmer.to_dict(),
        "stats": {
            "total_evaluations": total_evals,
            "grade_a_count": grade_a_total,
            "urs_count": urs_total,
            "rejected_count": rejected_total,
            "total_onions": total_onions_all,
            "grade_a_pct": round((grade_a_total / total_onions_all * 100) if total_onions_all else 0, 1),
            "urs_pct": round((urs_total / total_onions_all * 100) if total_onions_all else 0, 1),
            "rejected_pct": round((rejected_total / total_onions_all * 100) if total_onions_all else 0, 1)
        },
        "latest_evaluation": latest_eval,
        "current_market_price": market_price,
        "recent_reports": [e.to_dict() for e in evaluations[:5]]
    }), 200


@farmer_bp.route("/reports", methods=["GET"])
@login_required
@role_required("farmer")
def get_reports():
    user = get_current_user()
    farmer = user.farmer_profile
    if not farmer:
        return jsonify({"success": False, "error": "Farmer profile not found."}), 404

    search_query = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "").strip()
    grade_filter = request.args.get("grade", "").strip()

    query = Evaluation.query.filter_by(farmer_id=farmer.id, status="confirmed")

    if search_query:
        query = query.filter(Evaluation.report_id.ilike(f"%{search_query}%"))
    if status_filter:
        query = query.filter(Evaluation.status == status_filter)
    if grade_filter:
        if grade_filter == "Grade A":
            query = query.filter(Evaluation.overall_result.ilike("%Grade A%"))
        elif grade_filter == "URS":
            query = query.filter(Evaluation.overall_result.ilike("%URS%"))
        elif grade_filter == "Rejected":
            query = query.filter(Evaluation.overall_result.ilike("%Rejection%"))

    evals = query.order_by(Evaluation.evaluation_date.desc()).all()
    return jsonify({
        "success": True,
        "total": len(evals),
        "reports": [e.to_dict() for e in evals]
    }), 200


@farmer_bp.route("/reports/<report_identifier>", methods=["GET"])
@login_required
@role_required("farmer")
def get_report_detail(report_identifier):
    user = get_current_user()
    farmer = user.farmer_profile

    # Look up by report_id (e.g. ONR-2026-000124) or primary key id
    eval_record = None
    if report_identifier.isdigit():
        eval_record = Evaluation.query.filter_by(id=int(report_identifier)).first()
    if not eval_record:
        eval_record = Evaluation.query.filter_by(report_id=report_identifier).first()

    if not eval_record:
        return jsonify({"success": False, "error": "Report not found."}), 404

    # STRICT ACCESS CONTROL: Farmer can only access their OWN reports!
    if eval_record.farmer_id != farmer.id:
        return jsonify({
            "success": False,
            "error": "Access denied. You do not have permission to view this report."
        }), 403

    return jsonify({
        "success": True,
        "report": eval_record.to_dict()
    }), 200
