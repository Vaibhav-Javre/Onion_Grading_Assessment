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

    # Relationships
    user = db.relationship("User", back_populates="officer_profile")
    evaluations = db.relationship("Evaluation", back_populates="officer")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "officer_id": self.officer_id,
            "name": self.user.name if self.user else "",
            "phone": self.user.phone if self.user else "",
            "email": self.user.email if self.user else "",
            "procurement_center": self.procurement_center,
            "location": self.location,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<OfficerProfile {self.officer_id}: {self.procurement_center}>"
