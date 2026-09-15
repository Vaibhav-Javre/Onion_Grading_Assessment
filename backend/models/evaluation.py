from datetime import datetime, timezone

from backend.database.db import db


class Evaluation(db.Model):
    __tablename__ = "evaluations"

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.String(50), unique=True, nullable=True, index=True)  # e.g., ONR-2026-000124
    farmer_id = db.Column(db.Integer, db.ForeignKey("farmer_profiles.id", ondelete="CASCADE"), nullable=False)
    officer_id = db.Column(db.Integer, db.ForeignKey("officer_profiles.id"), nullable=False)
    
    # Image Paths (stores primary / first image for backward compatibility)
    original_image_path = db.Column(db.String(255), nullable=False)
    annotated_image_path = db.Column(db.String(255), nullable=False)
    total_images = db.Column(db.Integer, default=1, nullable=False)
    
    # Aggregated Counts across all images/angles
    total_onions = db.Column(db.Integer, default=0, nullable=False)
    healthy_count = db.Column(db.Integer, default=0, nullable=False)
    damaged_count = db.Column(db.Integer, default=0, nullable=False)
    rotten_count = db.Column(db.Integer, default=0, nullable=False)
    sprouted_count = db.Column(db.Integer, default=0, nullable=False)
    uncertain_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Grading results
    grade_a_count = db.Column(db.Integer, default=0, nullable=False)
    urs_count = db.Column(db.Integer, default=0, nullable=False)
    rejected_count = db.Column(db.Integer, default=0, nullable=False)
    
    overall_result = db.Column(db.String(100), default="Standard")
    quality_summary = db.Column(db.Text, nullable=True)
    
    # Market Price Estimation Snapshot & Procurement Metrics
    mandi_name = db.Column(db.String(120), default="Lasalgaon APMC Mandi", nullable=True)
    mandi_modal_price = db.Column(db.Float, nullable=True)
    mandi_price_date = db.Column(db.String(60), nullable=True)
    mandi_api_source = db.Column(db.String(255), default="data.gov.in", nullable=True)
    quality_score = db.Column(db.Float, nullable=True)
    estimated_price_per_quintal = db.Column(db.Float, nullable=True)
    quantity_quintals = db.Column(db.Float, default=0.0, nullable=True)
    total_payout = db.Column(db.Float, default=0.0, nullable=True)

    evaluation_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    status = db.Column(db.String(30), default="pending_confirmation")  # pending_confirmation, confirmed
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    farmer = db.relationship("FarmerProfile", back_populates="evaluations")
    officer = db.relationship("OfficerProfile", back_populates="evaluations")
    images = db.relationship("EvaluationImage", back_populates="evaluation", cascade="all, delete-orphan", order_by="EvaluationImage.image_order")
    items = db.relationship("EvaluationItem", back_populates="evaluation", cascade="all, delete-orphan")
    report = db.relationship("Report", back_populates="evaluation", uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        healthy_pct = round((self.healthy_count / self.total_onions * 100) if self.total_onions else 0, 1)
        damaged_pct = round((self.damaged_count / self.total_onions * 100) if self.total_onions else 0, 1)
        rotten_pct = round((self.rotten_count / self.total_onions * 100) if self.total_onions else 0, 1)
        sprouted_pct = round((self.sprouted_count / self.total_onions * 100) if self.total_onions else 0, 1)
        
        grade_a_pct = round((self.grade_a_count / self.total_onions * 100) if self.total_onions else 0, 1)
        urs_pct = round((self.urs_count / self.total_onions * 100) if self.total_onions else 0, 1)
        rejected_pct = round((self.rejected_count / self.total_onions * 100) if self.total_onions else 0, 1)

        return {
            "id": self.id,
            "report_id": self.report_id,
            "farmer": self.farmer.to_dict() if self.farmer else None,
            "officer": self.officer.to_dict() if self.officer else None,
            "original_image_path": self.original_image_path,
            "annotated_image_path": self.annotated_image_path,
            "total_images": self.total_images or 1,
            "images": [img.to_dict() for img in self.images],
            "total_onions": self.total_onions,
            "healthy": {"count": self.healthy_count, "percentage": healthy_pct},
            "damaged": {"count": self.damaged_count, "percentage": damaged_pct},
            "rotten": {"count": self.rotten_count, "percentage": rotten_pct},
            "sprouted": {"count": self.sprouted_count, "percentage": sprouted_pct},
            "uncertain": {"count": self.uncertain_count},
            "grade_a": {"count": self.grade_a_count, "percentage": grade_a_pct},
            "urs": {"count": self.urs_count, "percentage": urs_pct},
            "rejected": {"count": self.rejected_count, "percentage": rejected_pct},
            "overall_result": self.overall_result,
            "quality_summary": self.quality_summary,
            "price_estimation": {
                "mandi_name": self.mandi_name or "Lasalgaon APMC Mandi",
                "mandi_modal_price": self.mandi_modal_price,
                "mandi_price_date": self.mandi_price_date,
                "mandi_api_source": self.mandi_api_source or "data.gov.in",
                "quality_score_pct": self.quality_score,
                "estimated_price_per_quintal": self.estimated_price_per_quintal,
                "quantity_quintals": self.quantity_quintals or 0.0,
                "total_payout": self.total_payout or 0.0,
                "unit": "₹/Quintal"
            },
            "evaluation_date": self.evaluation_date.strftime("%d/%m/%Y %I:%M %p") if self.evaluation_date else "",
            "status": self.status,
            "has_pdf": bool(self.report and self.report.pdf_path),
            "pdf_url": f"/api/reports/{self.report_id}/pdf" if self.report_id and self.report else None,
            "items": [item.to_dict() for item in self.items]
        }

    def __repr__(self):
        return f"<Evaluation {self.report_id or self.id}: {self.total_onions} onions across {self.total_images} images>"


class EvaluationImage(db.Model):
    __tablename__ = "evaluation_images"

    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False)
    image_order = db.Column(db.Integer, default=1, nullable=False)
    original_image_path = db.Column(db.String(255), nullable=False)
    annotated_image_path = db.Column(db.String(255), nullable=False)
    
    # Per-image counts
    total_onions = db.Column(db.Integer, default=0, nullable=False)
    healthy_count = db.Column(db.Integer, default=0, nullable=False)
    damaged_count = db.Column(db.Integer, default=0, nullable=False)
    rotten_count = db.Column(db.Integer, default=0, nullable=False)
    sprouted_count = db.Column(db.Integer, default=0, nullable=False)
    uncertain_count = db.Column(db.Integer, default=0, nullable=False)

    # Relationship
    evaluation = db.relationship("Evaluation", back_populates="images")

    def to_dict(self):
        import os
        return {
            "id": self.id,
            "image_order": self.image_order,
            "original_image_path": self.original_image_path,
            "annotated_image_path": self.annotated_image_path,
            "original_filename": os.path.basename(self.original_image_path),
            "annotated_filename": os.path.basename(self.annotated_image_path),
            "annotated_url": f"/outputs/{os.path.basename(self.annotated_image_path)}",
            "total_onions": self.total_onions,
            "healthy_count": self.healthy_count,
            "damaged_count": self.damaged_count,
            "rotten_count": self.rotten_count,
            "sprouted_count": self.sprouted_count,
            "uncertain_count": self.uncertain_count
        }


class EvaluationItem(db.Model):
    __tablename__ = "evaluation_items"

    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False)
    image_order = db.Column(db.Integer, default=1, nullable=True)
    onion_number = db.Column(db.Integer, nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    classification_confidence = db.Column(db.Float, default=0.0)
    detection_confidence = db.Column(db.Float, default=0.0)
    x1 = db.Column(db.Integer, nullable=False)
    y1 = db.Column(db.Integer, nullable=False)
    x2 = db.Column(db.Integer, nullable=False)
    y2 = db.Column(db.Integer, nullable=False)

    # Relationship
    evaluation = db.relationship("Evaluation", back_populates="items")

    def to_dict(self):
        return {
            "id": self.id,
            "image_order": self.image_order or 1,
            "onion_number": self.onion_number,
            "class_name": self.class_name,
            "classification_confidence": round(self.classification_confidence, 3),
            "detection_confidence": round(self.detection_confidence, 3),
            "bounding_box": [self.x1, self.y1, self.x2, self.y2]
        }
