from datetime import datetime, timezone

from backend.database.db import db


class ProcurementTransaction(db.Model):
    __tablename__ = "procurement_transactions"

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(50), unique=True, nullable=False, index=True)  # e.g., TXN-2026-000101
    evaluation_id = db.Column(db.Integer, db.ForeignKey("evaluations.id", ondelete="CASCADE"), unique=True, nullable=False)
    report_id = db.Column(db.String(50), nullable=False, index=True)                    # e.g., ONR-2026-001089
    farmer_id = db.Column(db.Integer, db.ForeignKey("farmer_profiles.id"), nullable=False, index=True)
    officer_id = db.Column(db.Integer, db.ForeignKey("officer_profiles.id"), nullable=False, index=True)

    # Center & Location details
    procurement_center = db.Column(db.String(150), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    taluka = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=False, default="Maharashtra")

    # Evaluation Timestamps
    transaction_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Quantity & Counts
    total_onions = db.Column(db.Integer, default=0, nullable=False)
    healthy_count = db.Column(db.Integer, default=0, nullable=False)
    damaged_count = db.Column(db.Integer, default=0, nullable=False)
    rotten_count = db.Column(db.Integer, default=0, nullable=False)
    sprouted_count = db.Column(db.Integer, default=0, nullable=False)

    # Grades
    grade_a_count = db.Column(db.Integer, default=0, nullable=False)
    urs_count = db.Column(db.Integer, default=0, nullable=False)
    rejected_count = db.Column(db.Integer, default=0, nullable=False)

    # Percentages
    grade_a_pct = db.Column(db.Float, default=0.0)
    urs_pct = db.Column(db.Float, default=0.0)
    rejected_pct = db.Column(db.Float, default=0.0)
    healthy_pct = db.Column(db.Float, default=0.0)
    damaged_pct = db.Column(db.Float, default=0.0)
    rotten_pct = db.Column(db.Float, default=0.0)
    sprouted_pct = db.Column(db.Float, default=0.0)

    # Final result & Summary
    final_result = db.Column(db.String(100), nullable=False)
    quality_summary = db.Column(db.Text, nullable=True)

    # Market Price & Payout
    mandi_name = db.Column(db.String(120), nullable=True)
    market_price = db.Column(db.Float, nullable=True)                  # Modal price in ₹/Quintal
    estimated_rate_per_quintal = db.Column(db.Float, nullable=True)    # Quality adjusted price in ₹/Quintal
    quantity_quintals = db.Column(db.Float, default=0.0, nullable=True)
    total_payout = db.Column(db.Float, default=0.0, nullable=True)     # ₹ total calculated payout

    # PDF Document
    pdf_path = db.Column(db.String(255), nullable=True)

    # Audit timestamp
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    evaluation = db.relationship("Evaluation", backref=db.backref("transaction", uselist=False))
    farmer = db.relationship("FarmerProfile", backref="transactions")
    officer = db.relationship("OfficerProfile", backref="transactions")

    def to_dict(self):
        farmer_data = self.farmer.to_dict() if self.farmer else {}
        officer_data = self.officer.to_dict() if self.officer else {}

        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "report_id": self.report_id,
            "evaluation_id": self.evaluation_id,
            "transaction_date": self.transaction_date.strftime("%d/%m/%Y %I:%M %p") if self.transaction_date else "",
            "iso_date": self.transaction_date.isoformat() if self.transaction_date else None,
            "farmer": {
                "id": self.farmer_id,
                "farmer_id": farmer_data.get("farmer_id", ""),
                "name": farmer_data.get("name", ""),
                "phone": farmer_data.get("phone", ""),
                "village": self.village_name or farmer_data.get("village", ""),
                "taluka": self.taluka or farmer_data.get("taluka", ""),
                "district": self.district or farmer_data.get("district", ""),
                "state": self.state or farmer_data.get("state", "Maharashtra")
            },
            "officer": {
                "id": self.officer_id,
                "officer_id": officer_data.get("officer_id", ""),
                "name": officer_data.get("name", ""),
                "procurement_center": self.procurement_center,
                "location": officer_data.get("location", "")
            },
            "procurement_center": self.procurement_center,
            "district": self.district,
            "taluka": self.taluka or "",
            "state": self.state,
            "counts": {
                "total_onions": self.total_onions,
                "healthy": self.healthy_count,
                "damaged": self.damaged_count,
                "rotten": self.rotten_count,
                "sprouted": self.sprouted_count,
                "grade_a": self.grade_a_count,
                "urs": self.urs_count,
                "rejected": self.rejected_count
            },
            "percentages": {
                "grade_a": self.grade_a_pct,
                "urs": self.urs_pct,
                "rejected": self.rejected_pct,
                "healthy": self.healthy_pct,
                "damaged": self.damaged_pct,
                "rotten": self.rotten_pct,
                "sprouted": self.sprouted_pct
            },
            "final_result": self.final_result,
            "quality_summary": self.quality_summary,
            "economics": {
                "mandi_name": self.mandi_name,
                "market_price": round(self.market_price or 0.0, 2),
                "estimated_rate_per_quintal": round(self.estimated_rate_per_quintal or 0.0, 2),
                "quantity_quintals": round(self.quantity_quintals or 0.0, 2),
                "total_payout": round(self.total_payout or 0.0, 2)
            },
            "pdf_url": f"/api/reports/{self.report_id}/pdf" if self.report_id else None,
            "created_at": self.created_at.strftime("%d/%m/%Y %I:%M %p") if self.created_at else ""
        }

    @property
    def village_name(self):
        return self.farmer.village if self.farmer else ""

    def __repr__(self):
        return f"<ProcurementTransaction {self.transaction_id}: {self.final_result} (₹{self.total_payout})>"
