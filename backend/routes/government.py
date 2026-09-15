import csv
import io
from datetime import datetime, timezone

from flask import Blueprint, Response, jsonify, request

from backend.database.db import db
from backend.models.audit import AuditLog
from backend.models.evaluation import Evaluation
from backend.models.farmer import FarmerProfile
from backend.models.officer import OfficerProfile
from backend.models.transaction import ProcurementTransaction
from backend.models.user import User
from backend.services.market_price_service import MarketPriceService
from backend.utils.audit_helpers import record_audit_log
from backend.utils.auth_helpers import get_current_user, login_required, role_required

government_bp = Blueprint("government_bp", __name__, url_prefix="/api/government")


# =========================================================
# 1. GOVERNMENT DASHBOARD API
# =========================================================
@government_bp.route("/dashboard", methods=["GET"])
@login_required
@role_required("government", "admin")
def get_dashboard_data():
    """
    Returns high-level macro statistics for the Government Dashboard:
    - Total Farmers, Officers, Evaluations, Total Onions Evaluated
    - Grade A / URS / Rejected statistics
    - Total Procurement Centers
    - Recent Evaluations & Recent Transactions
    - Latest Mandi Market Prices
    - Quality Distribution & District-Wise Aggregations
    """
    total_farmers = FarmerProfile.query.count()
    total_officers = OfficerProfile.query.count()

    # Distinct procurement centers
    centers_query = db.session.query(OfficerProfile.procurement_center).distinct().all()
    procurement_centers = [c[0] for c in centers_query if c[0]]
    total_centers = len(procurement_centers)

    # Confirmed evaluations
    confirmed_evals = Evaluation.query.filter_by(status="confirmed").all()
    total_evaluations = len(confirmed_evals)

    total_onions = sum(e.total_onions or 0 for e in confirmed_evals)
    total_grade_a = sum(e.grade_a_count or 0 for e in confirmed_evals)
    total_urs = sum(e.urs_count or 0 for e in confirmed_evals)
    total_rejected = sum(e.rejected_count or 0 for e in confirmed_evals)

    total_healthy = sum(e.healthy_count or 0 for e in confirmed_evals)
    total_damaged = sum(e.damaged_count or 0 for e in confirmed_evals)
    total_rotten = sum(e.rotten_count or 0 for e in confirmed_evals)
    total_sprouted = sum(e.sprouted_count or 0 for e in confirmed_evals)

    grade_a_pct = round((total_grade_a / total_onions * 100) if total_onions else 0.0, 1)
    urs_pct = round((total_urs / total_onions * 100) if total_onions else 0.0, 1)
    rejected_pct = round((total_rejected / total_onions * 100) if total_onions else 0.0, 1)

    # Total quantity & payout across confirmed transactions
    all_txns = ProcurementTransaction.query.all()
    total_payout = sum(t.total_payout or 0.0 for t in all_txns)
    total_quintals = sum(t.quantity_quintals or 0.0 for t in all_txns)

    # Recent evaluations (latest 10)
    recent_eval_records = Evaluation.query.filter_by(status="confirmed")\
        .order_by(Evaluation.evaluation_date.desc(), Evaluation.id.desc())\
        .limit(10).all()
    recent_evaluations = [e.to_dict() for e in recent_eval_records]

    # Recent transactions (latest 10)
    recent_txn_records = ProcurementTransaction.query\
        .order_by(ProcurementTransaction.transaction_date.desc(), ProcurementTransaction.id.desc())\
        .limit(10).all()
    recent_transactions = [t.to_dict() for t in recent_txn_records]

    # Latest Mandi Prices (Benchmark APMC Mandis)
    market_prices = MarketPriceService.get_market_prices()

    # District-wise evaluation count & onions
    district_counts = {}
    for ev in confirmed_evals:
        dist = "Unknown"
        if ev.farmer and ev.farmer.district:
            dist = ev.farmer.district
        elif ev.officer and ev.officer.location:
            dist = ev.officer.location.split(",")[-1].strip()
        
        if dist not in district_counts:
            district_counts[dist] = {
                "district": dist,
                "evaluations": 0,
                "total_onions": 0,
                "grade_a": 0,
                "urs": 0,
                "rejected": 0
            }
        district_counts[dist]["evaluations"] += 1
        district_counts[dist]["total_onions"] += (ev.total_onions or 0)
        district_counts[dist]["grade_a"] += (ev.grade_a_count or 0)
        district_counts[dist]["urs"] += (ev.urs_count or 0)
        district_counts[dist]["rejected"] += (ev.rejected_count or 0)

    # Center-wise performance
    center_counts = {}
    for ev in confirmed_evals:
        c_name = ev.officer.procurement_center if (ev.officer and ev.officer.procurement_center) else "Default Mandi"
        if c_name not in center_counts:
            center_counts[c_name] = {
                "center": c_name,
                "evaluations": 0,
                "total_onions": 0,
                "grade_a": 0,
                "urs": 0,
                "rejected": 0
            }
        center_counts[c_name]["evaluations"] += 1
        center_counts[c_name]["total_onions"] += (ev.total_onions or 0)
        center_counts[c_name]["grade_a"] += (ev.grade_a_count or 0)
        center_counts[c_name]["urs"] += (ev.urs_count or 0)
        center_counts[c_name]["rejected"] += (ev.rejected_count or 0)

    # Record audit log for dashboard access
    user = get_current_user()
    record_audit_log(
        action="VIEW_DASHBOARD",
        entity_type="government_dashboard",
        entity_id="macro_kpi",
        details={"user": user.name if user else "Admin"},
        user=user
    )

    return jsonify({
        "success": True,
        "summary": {
            "total_farmers": total_farmers,
            "total_officers": total_officers,
            "total_centers": total_centers,
            "total_evaluations": total_evaluations,
            "total_onions": total_onions,
            "total_payout": round(total_payout, 2),
            "total_quintals": round(total_quintals, 2),
            "grades": {
                "grade_a": {"count": total_grade_a, "percentage": grade_a_pct},
                "urs": {"count": total_urs, "percentage": urs_pct},
                "rejected": {"count": total_rejected, "percentage": rejected_pct}
            },
            "classes": {
                "healthy": {"count": total_healthy, "percentage": round((total_healthy / total_onions * 100) if total_onions else 0.0, 1)},
                "damaged": {"count": total_damaged, "percentage": round((total_damaged / total_onions * 100) if total_onions else 0.0, 1)},
                "rotten": {"count": total_rotten, "percentage": round((total_rotten / total_onions * 100) if total_onions else 0.0, 1)},
                "sprouted": {"count": total_sprouted, "percentage": round((total_sprouted / total_onions * 100) if total_onions else 0.0, 1)}
            }
        },
        "recent_evaluations": recent_evaluations,
        "recent_transactions": recent_transactions,
        "market_prices": market_prices[:6] if market_prices else [],
        "district_stats": list(district_counts.values()),
        "center_stats": list(center_counts.values())
    }), 200


# =========================================================
# 2. FARMER RECORDS & DIRECTORY
# =========================================================
@government_bp.route("/farmers", methods=["GET"])
@login_required
@role_required("government", "admin")
def list_farmers():
    """
    Returns list of all farmers with evaluation summary, grade history, and location.
    Filters: search (name, mobile, farmer_id, village), district.
    """
    search_query = request.args.get("search", "").strip().lower()
    district_filter = request.args.get("district", "").strip()

    farmers = FarmerProfile.query.all()
    results = []

    for f in farmers:
        user = f.user
        name = user.name if user else ""
        phone = user.phone if user else ""
        farmer_id = f.farmer_id

        # Text filtering
        if search_query:
            match = (
                search_query in farmer_id.lower() or
                search_query in name.lower() or
                search_query in phone.lower() or
                search_query in (f.village or "").lower() or
                search_query in (f.district or "").lower()
            )
            if not match:
                continue

        if district_filter and district_filter.lower() != "all" and f.district.lower() != district_filter.lower():
            continue

        evals = [e for e in f.evaluations if e.status == "confirmed"]
        total_evals = len(evals)
        total_onions = sum(e.total_onions or 0 for e in evals)
        grade_a = sum(e.grade_a_count or 0 for e in evals)
        urs = sum(e.urs_count or 0 for e in evals)
        rejected = sum(e.rejected_count or 0 for e in evals)

        latest_eval = None
        if evals:
            evals_sorted = sorted(evals, key=lambda x: x.evaluation_date or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
            latest_eval = evals_sorted[0].evaluation_date.strftime("%d/%m/%Y") if evals_sorted[0].evaluation_date else ""

        results.append({
            "id": f.id,
            "farmer_id": f.farmer_id,
            "name": name,
            "phone": phone,
            "email": user.email if user else "",
            "village": f.village,
            "taluka": f.taluka,
            "district": f.district,
            "state": f.state,
            "total_evaluations": total_evals,
            "total_onions": total_onions,
            "grades": {
                "grade_a": grade_a,
                "urs": urs,
                "rejected": rejected
            },
            "latest_evaluation_date": latest_eval or "None",
            "registered_date": f.created_at.strftime("%d/%m/%Y") if f.created_at else ""
        })

    return jsonify({"success": True, "count": len(results), "farmers": results}), 200


@government_bp.route("/farmers/<int:farmer_id>", methods=["GET"])
@login_required
@role_required("government", "admin")
def get_farmer_detail(farmer_id):
    """
    Returns complete profile and full evaluation/transaction history for a specific farmer.
    """
    farmer = db.session.get(FarmerProfile, farmer_id)
    if not farmer:
        return jsonify({"success": False, "error": "Farmer not found."}), 404

    evals = [e.to_dict() for e in farmer.evaluations if e.status == "confirmed"]
    txns = [t.to_dict() for t in farmer.transactions]

    record_audit_log(
        action="VIEW_FARMER_RECORD",
        entity_type="farmer",
        entity_id=farmer.farmer_id,
        details={"farmer_name": farmer.user.name if farmer.user else ""}
    )

    return jsonify({
        "success": True,
        "farmer": farmer.to_dict(),
        "evaluations": evals,
        "transactions": txns
    }), 200


# =========================================================
# 3. OFFICER RECORDS & DIRECTORY
# =========================================================
@government_bp.route("/officers", methods=["GET"])
@login_required
@role_required("government", "admin")
def list_officers():
    """
    Returns list of all procurement officers with center info, evaluations performed, and activity stats.
    """
    search_query = request.args.get("search", "").strip().lower()
    officers = OfficerProfile.query.all()
    results = []

    for o in officers:
        user = o.user
        name = user.name if user else ""
        officer_id = o.officer_id
        center = o.procurement_center
        location = o.location

        if search_query:
            match = (
                search_query in officer_id.lower() or
                search_query in name.lower() or
                search_query in (user.phone or "").lower() or
                search_query in center.lower() or
                search_query in location.lower()
            )
            if not match:
                continue

        evals = [e for e in o.evaluations if e.status == "confirmed"]
        total_evals = len(evals)
        reports_generated = len([e for e in evals if e.report is not None])
        total_onions = sum(e.total_onions or 0 for e in evals)

        last_eval_date = ""
        if evals:
            evals_sorted = sorted(evals, key=lambda x: x.evaluation_date or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
            last_eval_date = evals_sorted[0].evaluation_date.strftime("%d/%m/%Y %I:%M %p") if evals_sorted[0].evaluation_date else ""

        results.append({
            "id": o.id,
            "officer_id": o.officer_id,
            "name": name,
            "email": user.email if user else "",
            "phone": user.phone if user else "",
            "procurement_center": center,
            "location": location,
            "total_evaluations": total_evals,
            "reports_generated": reports_generated,
            "total_onions": total_onions,
            "last_active": last_eval_date or "No evaluations yet"
        })

    return jsonify({"success": True, "count": len(results), "officers": results}), 200


@government_bp.route("/officers/<int:officer_id>", methods=["GET"])
@login_required
@role_required("government", "admin")
def get_officer_detail(officer_id):
    """
    Returns complete profile and activity history for a specific officer.
    """
    officer = db.session.get(OfficerProfile, officer_id)
    if not officer:
        return jsonify({"success": False, "error": "Officer not found."}), 404

    evals = [e.to_dict() for e in officer.evaluations if e.status == "confirmed"]
    txns = [t.to_dict() for t in officer.transactions]

    record_audit_log(
        action="VIEW_OFFICER_RECORD",
        entity_type="officer",
        entity_id=officer.officer_id,
        details={"officer_name": officer.user.name if officer.user else "", "center": officer.procurement_center}
    )

    return jsonify({
        "success": True,
        "officer": officer.to_dict(),
        "evaluations": evals,
        "transactions": txns
    }), 200


# =========================================================
# 4. DIGITAL PROCUREMENT TRANSACTIONS RECORD
# =========================================================
@government_bp.route("/transactions", methods=["GET"])
@login_required
@role_required("government", "admin")
def list_transactions():
    """
    Returns list of digital procurement transactions with comprehensive filtering.
    Filters: search, farmer_id, officer_id, center, district, result, from_date, to_date.
    Supports CSV export: ?export=csv
    """
    search = request.args.get("search", "").strip().lower()
    farmer_query = request.args.get("farmer_id", "").strip().lower()
    officer_query = request.args.get("officer_id", "").strip().lower()
    center_filter = request.args.get("center", "").strip().lower()
    district_filter = request.args.get("district", "").strip().lower()
    result_filter = request.args.get("result", "").strip().lower()
    from_date = request.args.get("from_date", "").strip()
    to_date = request.args.get("to_date", "").strip()
    export_csv = request.args.get("export", "").lower() == "csv"

    query = ProcurementTransaction.query.order_by(ProcurementTransaction.transaction_date.desc())
    txns = query.all()
    filtered = []

    for t in txns:
        farmer_data = t.farmer.to_dict() if t.farmer else {}
        officer_data = t.officer.to_dict() if t.officer else {}

        # Search term across ID, Report, Farmer, Officer, Center, District
        if search:
            match = (
                search in t.transaction_id.lower() or
                search in t.report_id.lower() or
                search in farmer_data.get("name", "").lower() or
                search in farmer_data.get("farmer_id", "").lower() or
                search in farmer_data.get("phone", "").lower() or
                search in officer_data.get("name", "").lower() or
                search in officer_data.get("officer_id", "").lower() or
                search in (t.procurement_center or "").lower() or
                search in (t.district or "").lower()
            )
            if not match:
                continue

        if farmer_query and (farmer_query not in farmer_data.get("farmer_id", "").lower() and farmer_query not in farmer_data.get("name", "").lower()):
            continue
        if officer_query and (officer_query not in officer_data.get("officer_id", "").lower() and officer_query not in officer_data.get("name", "").lower()):
            continue
        if center_filter and center_filter != "all" and center_filter not in (t.procurement_center or "").lower():
            continue
        if district_filter and district_filter != "all" and district_filter not in (t.district or "").lower():
            continue
        if result_filter and result_filter != "all" and result_filter not in (t.final_result or "").lower():
            continue

        # Date range filtering
        if from_date and t.transaction_date:
            try:
                dt_from = datetime.strptime(from_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if t.transaction_date.replace(tzinfo=timezone.utc) < dt_from:
                    continue
            except ValueError:
                pass

        if to_date and t.transaction_date:
            try:
                dt_to = datetime.strptime(to_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
                if t.transaction_date.replace(tzinfo=timezone.utc) > dt_to:
                    continue
            except ValueError:
                pass

        filtered.append(t)

    # CSV Export
    if export_csv:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Transaction ID", "Report ID", "Date", "Farmer ID", "Farmer Name", "Mobile",
            "District", "Officer ID", "Officer Name", "Procurement Center",
            "Total Onions", "Healthy", "Damaged", "Rotten", "Sprouted",
            "Grade A", "URS", "Rejected", "Grade A %", "URS %", "Rejected %",
            "Final Result", "Mandi Price (Rs/Q)", "Quantity (Q)", "Total Payout (Rs)"
        ])
        for item in filtered:
            f_d = item.farmer.to_dict() if item.farmer else {}
            o_d = item.officer.to_dict() if item.officer else {}
            writer.writerow([
                item.transaction_id, item.report_id,
                item.transaction_date.strftime("%Y-%m-%d %H:%M") if item.transaction_date else "",
                f_d.get("farmer_id", ""), f_d.get("name", ""), f_d.get("phone", ""),
                item.district, o_d.get("officer_id", ""), o_d.get("name", ""), item.procurement_center,
                item.total_onions, item.healthy_count, item.damaged_count, item.rotten_count, item.sprouted_count,
                item.grade_a_count, item.urs_count, item.rejected_count,
                item.grade_a_pct, item.urs_pct, item.rejected_pct,
                item.final_result, item.market_price, item.quantity_quintals, item.total_payout
            ])

        record_audit_log("EXPORT_CSV", "transactions", details={"count": len(filtered)})
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=Government_Procurement_Transactions.csv"}
        )

    return jsonify({
        "success": True,
        "count": len(filtered),
        "transactions": [t.to_dict() for t in filtered]
    }), 200


@government_bp.route("/transactions/<string:transaction_identifier>", methods=["GET"])
@login_required
@role_required("government", "admin")
def get_transaction_detail(transaction_identifier):
    """
    Returns full digital procurement transaction details.
    """
    clean_id = transaction_identifier.strip()
    txn = ProcurementTransaction.query.filter_by(transaction_id=clean_id).first()
    if not txn and clean_id.isdigit():
        txn = db.session.get(ProcurementTransaction, int(clean_id))
    if not txn:
        txn = ProcurementTransaction.query.filter_by(report_id=clean_id).first()

    if not txn:
        return jsonify({"success": False, "error": f"Transaction '{transaction_identifier}' not found."}), 404

    record_audit_log(
        action="VIEW_TRANSACTION",
        entity_type="transaction",
        entity_id=txn.transaction_id,
        details={"report_id": txn.report_id, "payout": txn.total_payout}
    )

    return jsonify({"success": True, "transaction": txn.to_dict()}), 200


# =========================================================
# 5. REPORT MANAGEMENT
# =========================================================
@government_bp.route("/reports", methods=["GET"])
@login_required
@role_required("government", "admin")
def list_reports():
    """
    Returns list of all confirmed reports for government administration.
    Filters: search, farmer_id, officer_id, district, center, result, from_date, to_date.
    Supports CSV export: ?export=csv
    """
    search = request.args.get("search", "").strip().lower()
    farmer_query = request.args.get("farmer_id", "").strip().lower()
    officer_query = request.args.get("officer_id", "").strip().lower()
    center_filter = request.args.get("center", "").strip().lower()
    district_filter = request.args.get("district", "").strip().lower()
    result_filter = request.args.get("result", "").strip().lower()
    from_date = request.args.get("from_date", "").strip()
    to_date = request.args.get("to_date", "").strip()
    export_csv = request.args.get("export", "").lower() == "csv"

    evals = Evaluation.query.filter_by(status="confirmed").order_by(Evaluation.evaluation_date.desc()).all()
    filtered = []

    for ev in evals:
        farmer_data = ev.farmer.to_dict() if ev.farmer else {}
        officer_data = ev.officer.to_dict() if ev.officer else {}
        report_code = ev.report_id or f"ONR-{ev.id}"

        if search:
            match = (
                search in report_code.lower() or
                search in farmer_data.get("name", "").lower() or
                search in farmer_data.get("farmer_id", "").lower() or
                search in farmer_data.get("phone", "").lower() or
                search in officer_data.get("name", "").lower() or
                search in officer_data.get("officer_id", "").lower() or
                search in officer_data.get("procurement_center", "").lower() or
                search in farmer_data.get("district", "").lower() or
                search in (ev.overall_result or "").lower()
            )
            if not match:
                continue

        if farmer_query and (farmer_query not in farmer_data.get("farmer_id", "").lower() and farmer_query not in farmer_data.get("name", "").lower()):
            continue
        if officer_query and (officer_query not in officer_data.get("officer_id", "").lower() and officer_query not in officer_data.get("name", "").lower()):
            continue
        if center_filter and center_filter != "all" and center_filter not in officer_data.get("procurement_center", "").lower():
            continue
        if district_filter and district_filter != "all" and district_filter not in farmer_data.get("district", "").lower():
            continue
        if result_filter and result_filter != "all" and result_filter not in (ev.overall_result or "").lower():
            continue

        # Date range
        if from_date and ev.evaluation_date:
            try:
                dt_from = datetime.strptime(from_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if ev.evaluation_date.replace(tzinfo=timezone.utc) < dt_from:
                    continue
            except ValueError:
                pass

        if to_date and ev.evaluation_date:
            try:
                dt_to = datetime.strptime(to_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
                if ev.evaluation_date.replace(tzinfo=timezone.utc) > dt_to:
                    continue
            except ValueError:
                pass

        filtered.append(ev)

    if export_csv:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Report ID", "Date", "Farmer ID", "Farmer Name", "District",
            "Officer ID", "Officer Name", "Procurement Center",
            "Total Onions", "Grade A", "URS", "Rejected",
            "Grade A %", "URS %", "Rejected %", "Final Result",
            "Estimated Price (Rs/Q)", "Quantity (Q)", "Payout (Rs)"
        ])
        for ev in filtered:
            f_d = ev.farmer.to_dict() if ev.farmer else {}
            o_d = ev.officer.to_dict() if ev.officer else {}
            total = ev.total_onions or 1
            writer.writerow([
                ev.report_id or f"ONR-{ev.id}",
                ev.evaluation_date.strftime("%Y-%m-%d %H:%M") if ev.evaluation_date else "",
                f_d.get("farmer_id", ""), f_d.get("name", ""), f_d.get("district", ""),
                o_d.get("officer_id", ""), o_d.get("name", ""), o_d.get("procurement_center", ""),
                ev.total_onions, ev.grade_a_count, ev.urs_count, ev.rejected_count,
                round(ev.grade_a_count / total * 100, 1),
                round(ev.urs_count / total * 100, 1),
                round(ev.rejected_count / total * 100, 1),
                ev.overall_result, ev.estimated_price_per_quintal, ev.quantity_quintals, ev.total_payout
            ])

        record_audit_log("EXPORT_REPORTS_CSV", "reports", details={"count": len(filtered)})
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=Government_Reports_Registry.csv"}
        )

    return jsonify({
        "success": True,
        "count": len(filtered),
        "reports": [e.to_dict() for e in filtered]
    }), 200


# =========================================================
# 6. IMMUTABLE AUDIT LOGS
# =========================================================
@government_bp.route("/audit-logs", methods=["GET"])
@login_required
@role_required("government", "admin")
def list_audit_logs():
    """
    Returns audit log entries with filters for action, entity_type, actor_role, and date range.
    """
    action_filter = request.args.get("action", "").strip()
    actor_role_filter = request.args.get("actor_role", "").strip()
    entity_type_filter = request.args.get("entity_type", "").strip()
    from_date = request.args.get("from_date", "").strip()
    to_date = request.args.get("to_date", "").strip()

    query = AuditLog.query.order_by(AuditLog.timestamp.desc())

    if action_filter and action_filter != "all":
        query = query.filter_by(action=action_filter)
    if actor_role_filter and actor_role_filter != "all":
        query = query.filter_by(actor_role=actor_role_filter)
    if entity_type_filter and entity_type_filter != "all":
        query = query.filter_by(entity_type=entity_type_filter)

    logs = query.limit(200).all()
    filtered = []

    for item in logs:
        if from_date and item.timestamp:
            try:
                dt_from = datetime.strptime(from_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if item.timestamp.replace(tzinfo=timezone.utc) < dt_from:
                    continue
            except ValueError:
                pass
        if to_date and item.timestamp:
            try:
                dt_to = datetime.strptime(to_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
                if item.timestamp.replace(tzinfo=timezone.utc) > dt_to:
                    continue
            except ValueError:
                pass
        filtered.append(item.to_dict())

    return jsonify({
        "success": True,
        "count": len(filtered),
        "logs": filtered
    }), 200


# =========================================================
# 7. MACRO ANALYTICS FOR DATA VISUALIZATION
# =========================================================
@government_bp.route("/analytics", methods=["GET"])
@login_required
@role_required("government", "admin")
def get_analytics():
    """
    Returns aggregated charting data:
    - Grade distribution (Grade A, URS, Rejected)
    - Quality-class distribution (Healthy, Damaged, Rotten, Sprouted)
    - District-wise evaluations and onions
    - Procurement-center performance
    - Monthly evaluation trends
    - Farmer evaluation volume distribution
    """
    confirmed = Evaluation.query.filter_by(status="confirmed").all()

    total_ga = sum(e.grade_a_count or 0 for e in confirmed)
    total_urs = sum(e.urs_count or 0 for e in confirmed)
    total_rej = sum(e.rejected_count or 0 for e in confirmed)

    total_healthy = sum(e.healthy_count or 0 for e in confirmed)
    total_damaged = sum(e.damaged_count or 0 for e in confirmed)
    total_rotten = sum(e.rotten_count or 0 for e in confirmed)
    total_sprouted = sum(e.sprouted_count or 0 for e in confirmed)

    # Monthly trends (last 6 months)
    monthly = {}
    for e in confirmed:
        if e.evaluation_date:
            m_key = e.evaluation_date.strftime("%b %Y")
            if m_key not in monthly:
                monthly[m_key] = {"month": m_key, "evaluations": 0, "onions": 0, "grade_a": 0, "urs": 0, "rejected": 0}
            monthly[m_key]["evaluations"] += 1
            monthly[m_key]["onions"] += (e.total_onions or 0)
            monthly[m_key]["grade_a"] += (e.grade_a_count or 0)
            monthly[m_key]["urs"] += (e.urs_count or 0)
            monthly[m_key]["rejected"] += (e.rejected_count or 0)

    # District aggregations
    district_data = {}
    for e in confirmed:
        d = e.farmer.district if (e.farmer and e.farmer.district) else "Nashik"
        if d not in district_data:
            district_data[d] = {"district": d, "evaluations": 0, "onions": 0, "grade_a": 0, "urs": 0, "rejected": 0}
        district_data[d]["evaluations"] += 1
        district_data[d]["onions"] += (e.total_onions or 0)
        district_data[d]["grade_a"] += (e.grade_a_count or 0)
        district_data[d]["urs"] += (e.urs_count or 0)
        district_data[d]["rejected"] += (e.rejected_count or 0)

    # Center performance
    center_data = {}
    for e in confirmed:
        c = e.officer.procurement_center if (e.officer and e.officer.procurement_center) else "Lasalgaon Yard"
        if c not in center_data:
            center_data[c] = {"center": c, "evaluations": 0, "onions": 0, "grade_a": 0, "urs": 0, "rejected": 0}
        center_data[c]["evaluations"] += 1
        center_data[c]["onions"] += (e.total_onions or 0)
        center_data[c]["grade_a"] += (e.grade_a_count or 0)
        center_data[c]["urs"] += (e.urs_count or 0)
        center_data[c]["rejected"] += (e.rejected_count or 0)

    return jsonify({
        "success": True,
        "grade_distribution": {
            "labels": ["Grade A (Premium)", "URS Standard", "Rejected Bulbs"],
            "counts": [total_ga, total_urs, total_rej]
        },
        "quality_class_distribution": {
            "labels": ["Healthy", "Damaged", "Rotten", "Sprouted"],
            "counts": [total_healthy, total_damaged, total_rotten, total_sprouted]
        },
        "monthly_trends": list(monthly.values()),
        "district_stats": list(district_data.values()),
        "center_stats": list(center_data.values())
    }), 200


# =========================================================
# 8. GLOBAL OMNI-SEARCH
# =========================================================
@government_bp.route("/search", methods=["GET"])
@login_required
@role_required("government", "admin")
def global_search():
    """
    Omni-search across Farmers, Officers, Transactions, Reports, Procurement Centers, and Districts.
    Query parameter: q
    """
    q = request.args.get("q", "").strip().lower()
    if not q or len(q) < 2:
        return jsonify({"success": True, "query": q, "results": {"farmers": [], "officers": [], "transactions": [], "reports": []}}), 200

    record_audit_log("GLOBAL_SEARCH", "search_query", details={"query": q})

    # Search Farmers
    all_farmers = FarmerProfile.query.all()
    matched_farmers = []
    for f in all_farmers:
        name = f.user.name if f.user else ""
        phone = f.user.phone if f.user else ""
        if (q in f.farmer_id.lower() or q in name.lower() or q in phone.lower() or
                q in (f.village or "").lower() or q in (f.district or "").lower()):
            matched_farmers.append({
                "farmer_id": f.farmer_id,
                "name": name,
                "phone": phone,
                "village": f.village,
                "district": f.district,
                "link": f"/government/farmers?search={f.farmer_id}"
            })

    # Search Officers
    all_officers = OfficerProfile.query.all()
    matched_officers = []
    for o in all_officers:
        name = o.user.name if o.user else ""
        if (q in o.officer_id.lower() or q in name.lower() or
                q in (o.procurement_center or "").lower() or q in (o.location or "").lower()):
            matched_officers.append({
                "officer_id": o.officer_id,
                "name": name,
                "procurement_center": o.procurement_center,
                "location": o.location,
                "link": f"/government/officers?search={o.officer_id}"
            })

    # Search Transactions
    all_txns = ProcurementTransaction.query.all()
    matched_txns = []
    for t in all_txns:
        f_name = t.farmer.user.name if (t.farmer and t.farmer.user) else ""
        f_id = t.farmer.farmer_id if t.farmer else ""
        if (q in t.transaction_id.lower() or q in t.report_id.lower() or
                q in f_id.lower() or q in f_name.lower() or
                q in (t.procurement_center or "").lower() or q in (t.district or "").lower()):
            matched_txns.append({
                "transaction_id": t.transaction_id,
                "report_id": t.report_id,
                "farmer_name": f_name,
                "final_result": t.final_result,
                "total_payout": t.total_payout,
                "date": t.transaction_date.strftime("%d/%m/%Y") if t.transaction_date else "",
                "link": f"/government/transactions?search={t.transaction_id}"
            })

    # Search Reports
    all_evals = Evaluation.query.filter_by(status="confirmed").all()
    matched_reports = []
    for ev in all_evals:
        r_code = ev.report_id or f"ONR-{ev.id}"
        f_name = ev.farmer.user.name if (ev.farmer and ev.farmer.user) else ""
        f_id = ev.farmer.farmer_id if ev.farmer else ""
        o_center = ev.officer.procurement_center if ev.officer else ""
        if (q in r_code.lower() or q in f_id.lower() or q in f_name.lower() or
                q in o_center.lower() or q in (ev.overall_result or "").lower()):
            matched_reports.append({
                "report_id": r_code,
                "farmer_id": f_id,
                "farmer_name": f_name,
                "overall_result": ev.overall_result,
                "total_onions": ev.total_onions,
                "pdf_url": f"/api/reports/{r_code}/pdf",
                "link": f"/government/reports?search={r_code}"
            })

    return jsonify({
        "success": True,
        "query": q,
        "results": {
            "farmers": matched_farmers[:8],
            "officers": matched_officers[:8],
            "transactions": matched_txns[:8],
            "reports": matched_reports[:8]
        }
    }), 200
