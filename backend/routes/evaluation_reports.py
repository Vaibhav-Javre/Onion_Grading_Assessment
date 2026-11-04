import io
from flask import Blueprint, jsonify, request, Response, send_file
from backend.utils.auth_helpers import get_current_user, login_required, role_required
from backend.services.evaluation_report_service import EvaluationReportService

evaluation_reports_bp = Blueprint("evaluation_reports_bp", __name__, url_prefix="/api/evaluation-reports")


@evaluation_reports_bp.route("/analytics", methods=["GET"])
@login_required
def get_evaluation_analytics():
    """
    Returns full evaluation report analytics:
    - Summary metrics (total onions vs total evaluations, farmers, officers, grades)
    - Quality distribution (Healthy, Damaged, Rotten, Sprouted)
    - Daily evaluation trend (0 for empty dates)
    - Weekly and Monthly evaluation comparison trends
    - Period comparison (Current vs Previous with % change)
    - Procurement center activity breakdown
    - Officer evaluation activity
    - Farmer evaluation history
    Scoped strictly by user role.
    """
    user = get_current_user()
    role = user.role if user else "farmer"

    period = request.args.get("period", "this_month")
    start_date = request.args.get("start_date", "").strip() or None
    end_date = request.args.get("end_date", "").strip() or None
    center = request.args.get("center", "").strip() or None
    officer_id = request.args.get("officer_id", "").strip() or None
    farmer_id = request.args.get("farmer_id", "").strip() or None
    grade = request.args.get("grade", "").strip() or None
    weeks = int(request.args.get("weeks", 4))
    months = int(request.args.get("months", 6))

    try:
        data = EvaluationReportService.get_analytics(
            period=period,
            start_date=start_date,
            end_date=end_date,
            role=role,
            user=user,
            center=center,
            officer_id=officer_id,
            farmer_id=farmer_id,
            grade=grade,
            trend_weeks=weeks,
            trend_months=months
        )
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to compute evaluation analytics: {e!s}"}), 500


@evaluation_reports_bp.route("/records", methods=["GET"])
@login_required
def get_evaluation_records():
    """
    Returns detailed confirmed evaluation records with search & filters.
    """
    user = get_current_user()
    role = user.role if user else "farmer"

    period = request.args.get("period", "this_month")
    start_date = request.args.get("start_date", "").strip() or None
    end_date = request.args.get("end_date", "").strip() or None
    center = request.args.get("center", "").strip() or None
    officer_id = request.args.get("officer_id", "").strip() or None
    farmer_id = request.args.get("farmer_id", "").strip() or None
    grade = request.args.get("grade", "").strip() or None
    search_q = request.args.get("search", "").strip().lower()

    try:
        data = EvaluationReportService.get_analytics(
            period=period,
            start_date=start_date,
            end_date=end_date,
            role=role,
            user=user,
            center=center,
            officer_id=officer_id,
            farmer_id=farmer_id,
            grade=grade
        )
        records = data.get("records", [])

        if search_q:
            records = [
                r for r in records
                if search_q in r["report_id"].lower()
                or search_q in r["farmer_id"].lower()
                or search_q in r["farmer_name"].lower()
                or search_q in r["officer_id"].lower()
                or search_q in r["officer_name"].lower()
                or search_q in r["procurement_center"].lower()
            ]

        return jsonify({
            "success": True,
            "total": len(records),
            "records": records
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to fetch records: {e!s}"}), 500


@evaluation_reports_bp.route("/export/csv", methods=["GET"])
@login_required
def export_csv():
    """Exports current report as a downloadable CSV file."""
    user = get_current_user()
    role = user.role if user else "farmer"

    period = request.args.get("period", "this_month")
    start_date = request.args.get("start_date", "").strip() or None
    end_date = request.args.get("end_date", "").strip() or None

    csv_data = EvaluationReportService.export_csv(
        period=period,
        start_date=start_date,
        end_date=end_date,
        role=role,
        user=user
    )

    filename = f"OnionGrade_Report_{period}_{role}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@evaluation_reports_bp.route("/export/excel", methods=["GET"])
@login_required
def export_excel():
    """Exports current report as an Excel-compatible CSV stream with UTF-8 BOM."""
    user = get_current_user()
    role = user.role if user else "farmer"

    period = request.args.get("period", "this_month")
    start_date = request.args.get("start_date", "").strip() or None
    end_date = request.args.get("end_date", "").strip() or None

    excel_data = EvaluationReportService.export_excel(
        period=period,
        start_date=start_date,
        end_date=end_date,
        role=role,
        user=user
    )

    filename = f"OnionGrade_Report_{period}_{role}.csv"
    return Response(
        excel_data,
        mimetype="application/vnd.ms-excel; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@evaluation_reports_bp.route("/export/weekly-pdf", methods=["GET"])
@login_required
def export_weekly_pdf():
    """Generates and downloads official Weekly Evaluation Report PDF."""
    user = get_current_user()
    role = user.role if user else "farmer"

    try:
        filename, filepath, _size = EvaluationReportService.generate_pdf_report(
            report_type="weekly",
            period="this_week",
            role=role,
            user=user
        )
        return send_file(
            filepath,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to generate Weekly PDF: {e!s}"}), 500


@evaluation_reports_bp.route("/export/monthly-pdf", methods=["GET"])
@login_required
def export_monthly_pdf():
    """Generates and downloads official Monthly Evaluation Report PDF."""
    user = get_current_user()
    role = user.role if user else "farmer"

    try:
        filename, filepath, _size = EvaluationReportService.generate_pdf_report(
            report_type="monthly",
            period="this_month",
            role=role,
            user=user
        )
        return send_file(
            filepath,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to generate Monthly PDF: {e!s}"}), 500
