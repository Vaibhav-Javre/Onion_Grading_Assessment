import os
from flask import Blueprint, jsonify, request, send_file, abort, redirect, url_for
from backend.database.db import db
from backend.models.evaluation import Evaluation
from backend.models.report import Report
from backend.services.pdf_service import generate_evaluation_pdf
from backend.utils.auth_helpers import login_required, get_current_user

reports_bp = Blueprint("reports_bp", __name__)

def _resolve_evaluation(report_identifier):
    """
    Resolves an Evaluation record from various identifier formats:
    e.g. 'ONR-2026-000124', 'Onion_Report_ONR-2026-000124.pdf', '124', 'ONR-3'
    """
    if not report_identifier:
        return None

    clean_id = str(report_identifier).replace("Onion_Report_", "").replace(".pdf", "").replace(".PDF", "").strip()

    # Try exact report_id
    eval_record = Evaluation.query.filter_by(report_id=clean_id).first()
    if eval_record:
        return eval_record

    # Try numeric ID
    if clean_id.isdigit():
        eval_record = db.session.get(Evaluation, int(clean_id))
        if eval_record:
            return eval_record

    # Try hyphenated suffix e.g. ONR-3
    if "-" in clean_id:
        suffix = clean_id.split("-")[-1]
        if suffix.isdigit():
            eval_record = db.session.get(Evaluation, int(suffix))
            if eval_record:
                return eval_record

    return None

def _get_evaluation_with_auth(report_identifier):
    """
    Finds evaluation and verifies authorization.
    """
    eval_record = _resolve_evaluation(report_identifier)
    if not eval_record:
        return None, (jsonify({"success": False, "error": f"Evaluation report '{report_identifier}' not found."}), 404)

    user = get_current_user()
    if user:
        if user.role == "farmer":
            if not user.farmer_profile or eval_record.farmer_id != user.farmer_profile.id:
                return None, (jsonify({
                    "success": False,
                    "error": "Access denied. You are not authorized to view reports belonging to other farmers."
                }), 403)
    # If no session, allow download if report is confirmed
    elif eval_record.status != "confirmed":
        return None, (jsonify({"success": False, "error": "Authentication required."}), 401)

    return eval_record, None


def _serve_pdf(eval_record, as_attachment=True):
    """Generates PDF if needed and sends via send_file with robust headers."""
    report = eval_record.report
    pdf_path = report.pdf_path if report else None

    if not pdf_path or not os.path.exists(pdf_path):
        try:
            pdf_fn, pdf_fp, pdf_size = generate_evaluation_pdf(eval_record)
            if not report:
                report = Report(evaluation_id=eval_record.id, pdf_path=pdf_fp, file_size_bytes=pdf_size)
                db.session.add(report)
            else:
                report.pdf_path = pdf_fp
                report.file_size_bytes = pdf_size
            db.session.commit()
            pdf_path = pdf_fp
        except Exception as e:
            return jsonify({"success": False, "error": f"Failed to generate PDF: {str(e)}"}), 500

    report_code = eval_record.report_id or f"ONR-{eval_record.id}"
    download_filename = f"Onion_Report_{report_code}.pdf"

    response = send_file(
        os.path.abspath(pdf_path),
        mimetype="application/pdf",
        as_attachment=as_attachment,
        download_name=download_filename
    )
    # Explicit RFC headers to guarantee Chrome, Edge, and Firefox treat it as a true PDF
    response.headers["Content-Type"] = "application/pdf"
    disp = "attachment" if as_attachment else "inline"
    response.headers["Content-Disposition"] = f'{disp}; filename="{download_filename}"'
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


# Direct Named PDF Download Route (e.g. /reports/download/Onion_Report_ONR-2026-000124.pdf)
@reports_bp.route("/reports/download/<path:filename>", methods=["GET"])
def download_by_filename(filename):
    eval_record, error_resp = _get_evaluation_with_auth(filename)
    if error_resp:
        return error_resp
    view_inline = request.args.get("view", "0") in ("1", "true") or request.args.get("inline", "0") in ("1", "true")
    return _serve_pdf(eval_record, as_attachment=not view_inline)

@reports_bp.route("/api/reports/download/<path:filename>", methods=["GET"])
def api_download_by_filename(filename):
    return download_by_filename(filename)

# Legacy / Alternative PDF Endpoints (Redirect directly to named .pdf URL so browsers always save with .pdf extension)
@reports_bp.route("/api/reports/<report_identifier>/pdf", methods=["GET"])
def api_download_pdf(report_identifier):
    eval_record, error_resp = _get_evaluation_with_auth(report_identifier)
    if error_resp:
        return error_resp
    report_code = eval_record.report_id or f"ONR-{eval_record.id}"
    view_inline = request.args.get("view", "0") in ("1", "true") or request.args.get("inline", "0") in ("1", "true")
    url = f"/reports/download/Onion_Report_{report_code}.pdf"
    if view_inline:
        url += "?inline=1"
    return redirect(url, code=302)

@reports_bp.route("/api/reports/<report_identifier>", methods=["GET"])
def api_get_report_or_pdf(report_identifier):
    if str(report_identifier).endswith(".pdf") or str(report_identifier).endswith(".PDF"):
        return api_download_pdf(report_identifier)
    eval_record, error_resp = _get_evaluation_with_auth(report_identifier)
    if error_resp:
        return error_resp
    return jsonify({"success": True, "report": eval_record.to_dict()}), 200

@reports_bp.route("/reports/<report_identifier>/pdf", methods=["GET"])
def public_download_pdf(report_identifier):
    return api_download_pdf(report_identifier)

@reports_bp.route("/reports/pdf/<report_identifier>", methods=["GET"])
def direct_download_pdf(report_identifier):
    return api_download_pdf(report_identifier)

@reports_bp.route("/farmer/report/<report_identifier>/pdf", methods=["GET"])
def farmer_download_pdf(report_identifier):
    return api_download_pdf(report_identifier)

@reports_bp.route("/officer/report/<report_identifier>/pdf", methods=["GET"])
def officer_download_pdf(report_identifier):
    return api_download_pdf(report_identifier)

