from datetime import datetime, timezone
from backend.database.db import db

class FarmerProfile(db.Model):
    __tablename__ = "farmer_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    farmer_id = db.Column(db.String(50), unique=True, nullable=False, index=True)  # e.g., FMR-2026-0001
    village = db.Column(db.String(100), nullable=False)
    taluka = db.Column(db.String(100), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False, default="Maharashtra")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = db.relationship("User", back_populates="farmer_profile")
    evaluations = db.relationship("Evaluation", back_populates="farmer", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "farmer_id": self.farmer_id,
            "name": self.user.name if self.user else "",
            "phone": self.user.phone if self.user else "",
            "email": self.user.email if self.user else "",
            "village": self.village,
            "taluka": self.taluka,
            "district": self.district,
            "state": self.state,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<FarmerProfile {self.farmer_id}: {self.user.name if self.user else 'No User'}>"
