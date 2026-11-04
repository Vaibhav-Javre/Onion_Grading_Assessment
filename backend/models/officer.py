from datetime import datetime, timezone

from backend.database.db import db


class OfficerProfile(db.Model):
    __tablename__ = "officer_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    officer_id = db.Column(db.String(50), unique=True, nullable=False, index=True)  # e.g., OFF-2026-001
    procurement_center = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False, default="Lasalgaon, Nashik")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Verification and Administrative Details
    status = db.Column(db.String(30), nullable=False, default="PENDING", index=True)  # PENDING, APPROVED, REJECTED
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    application_id = db.Column(db.String(50), unique=True, nullable=True, index=True)
    government_id_number = db.Column(db.String(100), nullable=True)
    id_proof_path = db.Column(db.String(255), nullable=True)
    center_address = db.Column(db.String(255), nullable=True)
    village = db.Column(db.String(100), nullable=True)
    taluka = db.Column(db.String(100), nullable=True)
    district = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True, default="Maharashtra")
    designation = db.Column(db.String(100), nullable=True, default="Procurement Officer")
    department = db.Column(db.String(150), nullable=True, default="APMC Mandi Board")
    experience_years = db.Column(db.String(50), nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    verified_by = db.Column(db.String(120), nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship("User", back_populates="officer_profile")
    evaluations = db.relationship("Evaluation", back_populates="officer")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "officer_id": self.officer_id,
            "application_id": self.application_id or self.officer_id,
            "name": self.user.name if self.user else "",
            "phone": self.user.phone if self.user else "",
            "email": self.user.email if self.user else "",
            "status": self.status or "PENDING",
            "is_active": bool(self.is_active),
            "procurement_center": self.procurement_center,
            "center_address": self.center_address or "",
            "location": self.location,
            "village": self.village or "",
            "taluka": self.taluka or "",
            "district": self.district or "",
            "state": self.state or "Maharashtra",
            "designation": self.designation or "Procurement Officer",
            "department": self.department or "APMC Mandi Board",
            "government_id_number": self.government_id_number or "",
            "id_proof_path": self.id_proof_path or "",
            "experience_years": self.experience_years or "",
            "rejection_reason": self.rejection_reason or "",
            "verified_by": self.verified_by or "",
            "verified_at": self.verified_at.strftime("%d/%m/%Y %I:%M %p") if self.verified_at else None,
            "created_at": self.created_at.strftime("%d/%m/%Y %I:%M %p") if self.created_at else None,
            "iso_created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<OfficerProfile {self.officer_id} ({self.status}): {self.procurement_center}>"


class OfficerFarmer(db.Model):
    __tablename__ = "officer_farmers"

    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey("officer_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey("farmer_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint("officer_id", "farmer_id", name="uq_officer_farmer"),
    )

    officer = db.relationship("OfficerProfile", backref=db.backref("my_farmer_links", cascade="all, delete-orphan", lazy="dynamic"))
    farmer = db.relationship("FarmerProfile", backref=db.backref("officer_links", cascade="all, delete-orphan", lazy="dynamic"))

    def to_dict(self):
        farmer_data = self.farmer.to_dict() if self.farmer else {}
        farmer_data["added_to_officer_at"] = self.created_at.strftime("%d/%m/%Y %I:%M %p") if self.created_at else None
        farmer_data["iso_added_at"] = self.created_at.isoformat() if self.created_at else None
        farmer_data["officer_farmer_id"] = self.id
        return farmer_data

    def __repr__(self):
        return f"<OfficerFarmer officer={self.officer_id} farmer={self.farmer_id}>"

