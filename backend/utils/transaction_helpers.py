import random
from datetime import datetime, timezone

from backend.database.db import db
from backend.models.transaction import ProcurementTransaction
from backend.utils.audit_helpers import record_audit_log


def generate_transaction_id():
    """Generates unique Transaction ID like TXN-2026-000189"""
    year = datetime.now(timezone.utc).year
    count = db.session.query(ProcurementTransaction).count() + 1
    salt = random.randint(10, 99)
    while True:
        candidate = f"TXN-{year}-{count:04d}{salt:02d}"
        if not ProcurementTransaction.query.filter_by(transaction_id=candidate).first():
            return candidate
        count += 1
        salt = random.randint(10, 99)


def create_transaction_for_evaluation(evaluation, commit=True):
    """
    Creates a ProcurementTransaction record for a confirmed evaluation.
    Idempotent: if transaction already exists for this evaluation, returns existing.
    """
    if not evaluation or not evaluation.id:
        return None

    existing = ProcurementTransaction.query.filter_by(evaluation_id=evaluation.id).first()
    if existing:
        return existing

    farmer = evaluation.farmer
    officer = evaluation.officer

    total_onions = evaluation.total_onions or 0
    healthy_pct = round((evaluation.healthy_count / total_onions * 100) if total_onions else 0.0, 1)
    damaged_pct = round((evaluation.damaged_count / total_onions * 100) if total_onions else 0.0, 1)
    rotten_pct = round((evaluation.rotten_count / total_onions * 100) if total_onions else 0.0, 1)
    sprouted_pct = round((evaluation.sprouted_count / total_onions * 100) if total_onions else 0.0, 1)

    ga_pct = round((evaluation.grade_a_count / total_onions * 100) if total_onions else 0.0, 1)
    urs_pct = round((evaluation.urs_count / total_onions * 100) if total_onions else 0.0, 1)
    rej_pct = round((evaluation.rejected_count / total_onions * 100) if total_onions else 0.0, 1)

    txn_id = generate_transaction_id()
    pdf_path = evaluation.report.pdf_path if evaluation.report else None

    center_name = officer.procurement_center if officer else "APMC Mandi Yard"
    district = farmer.district if farmer else (officer.location.split(",")[-1].strip() if officer else "Nashik")
    taluka = farmer.taluka if farmer else ""
    state = farmer.state if farmer else "Maharashtra"

    txn = ProcurementTransaction(
        transaction_id=txn_id,
        evaluation_id=evaluation.id,
        report_id=evaluation.report_id or f"ONR-{evaluation.id}",
        farmer_id=evaluation.farmer_id,
        officer_id=evaluation.officer_id,
        procurement_center=center_name,
        district=district,
        taluka=taluka,
        state=state,
        transaction_date=evaluation.evaluation_date or datetime.now(timezone.utc),
        total_onions=total_onions,
        healthy_count=evaluation.healthy_count,
        damaged_count=evaluation.damaged_count,
        rotten_count=evaluation.rotten_count,
        sprouted_count=evaluation.sprouted_count,
        grade_a_count=evaluation.grade_a_count,
        urs_count=evaluation.urs_count,
        rejected_count=evaluation.rejected_count,
        grade_a_pct=ga_pct,
        urs_pct=urs_pct,
        rejected_pct=rej_pct,
        healthy_pct=healthy_pct,
        damaged_pct=damaged_pct,
        rotten_pct=rotten_pct,
        sprouted_pct=sprouted_pct,
        final_result=evaluation.overall_result or "Standard",
        quality_summary=evaluation.quality_summary,
        mandi_name=evaluation.mandi_name,
        market_price=evaluation.mandi_modal_price,
        estimated_rate_per_quintal=evaluation.estimated_price_per_quintal,
        quantity_quintals=evaluation.quantity_quintals or 0.0,
        total_payout=evaluation.total_payout or 0.0,
        pdf_path=pdf_path
    )

    db.session.add(txn)
    if commit:
        db.session.commit()

        # Audit logging
        record_audit_log(
            action="CREATE_TRANSACTION",
            entity_type="transaction",
            entity_id=txn.transaction_id,
            details={
                "report_id": txn.report_id,
                "farmer_id": farmer.farmer_id if farmer else None,
                "officer_id": officer.officer_id if officer else None,
                "total_onions": total_onions,
                "final_result": txn.final_result,
                "total_payout": txn.total_payout,
                "center": txn.procurement_center
            }
        )

    return txn
