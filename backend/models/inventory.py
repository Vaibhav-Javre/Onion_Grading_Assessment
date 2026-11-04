from datetime import datetime, timezone
from backend.database.db import db


class InventoryItem(db.Model):
    __tablename__ = "inventory_items"

    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.String(60), unique=True, nullable=False, index=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey("evaluations.id", ondelete="SET NULL"), nullable=True, index=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey("farmer_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    officer_id = db.Column(db.Integer, db.ForeignKey("officer_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    center_name = db.Column(db.String(120), default="Lasalgaon APMC Mandi", nullable=False, index=True)
    district = db.Column(db.String(100), default="Nashik", nullable=True)

    # Dates
    storage_start_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    evaluation_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Physical Quantities
    # 1 Quintal = 100 kg, 1 Tonne = 1000 kg = 10 Quintals
    quantity_kg = db.Column(db.Float, default=0.0, nullable=False)
    quantity_quintals = db.Column(db.Float, default=0.0, nullable=False)
    quantity_tonnes = db.Column(db.Float, default=0.0, nullable=False)

    # Quality breakdown in kg
    grade_a_kg = db.Column(db.Float, default=0.0, nullable=False)
    urs_kg = db.Column(db.Float, default=0.0, nullable=False)
    rejected_kg = db.Column(db.Float, default=0.0, nullable=False)

    # Current remaining balances in kg (decrement on dispatch/sale)
    current_balance_kg = db.Column(db.Float, default=0.0, nullable=False)
    grade_a_balance_kg = db.Column(db.Float, default=0.0, nullable=False)
    urs_balance_kg = db.Column(db.Float, default=0.0, nullable=False)
    rejected_balance_kg = db.Column(db.Float, default=0.0, nullable=False)

    # Evaluated bulb counts
    total_onions = db.Column(db.Integer, default=0)
    grade_a_count = db.Column(db.Integer, default=0)
    urs_count = db.Column(db.Integer, default=0)
    rejected_count = db.Column(db.Integer, default=0)

    # Overall grading category
    primary_category = db.Column(db.String(50), default="Grade A")
    status = db.Column(db.String(30), default="IN_STORAGE", nullable=False)  # IN_STORAGE, PARTIALLY_DISPATCHED, DEPLETED
    source = db.Column(db.String(60), default="EVALUATION_CONFIRMATION", nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    farmer = db.relationship("FarmerProfile", backref="inventory_items")
    officer = db.relationship("OfficerProfile", backref="inventory_items")
    evaluation = db.relationship("Evaluation", backref="inventory_item", uselist=False)
    movements = db.relationship("InventoryMovement", back_populates="inventory_item", cascade="all, delete-orphan", order_by="InventoryMovement.date.desc()")

    @property
    def storage_age_days(self):
        """Calculates days elapsed since storage start date."""
        if not self.storage_start_date:
            return 0
        now = datetime.now(timezone.utc)
        start = self.storage_start_date.replace(tzinfo=timezone.utc) if self.storage_start_date.tzinfo is None else self.storage_start_date
        diff = (now - start).total_seconds() / 86400.0
        return max(0, int(diff))

    def to_dict(self):
        return {
            "id": self.id,
            "inventory_id": self.id,
            "batch_id": self.batch_id,
            "evaluation_id": self.evaluation_id,
            "farmer_id": self.farmer_id,
            "farmer_name": self.farmer.user.name if self.farmer and self.farmer.user else "Farmer",
            "officer_id": self.officer_id,
            "officer_name": self.officer.user.name if self.officer and self.officer.user else "Officer",
            "center_name": self.center_name,
            "district": self.district,
            "storage_start_date": self.storage_start_date.strftime("%d/%m/%Y") if self.storage_start_date else None,
            "evaluation_date": self.evaluation_date.strftime("%d/%m/%Y") if self.evaluation_date else None,
            "storage_age_days": self.storage_age_days,
            "quantity_kg": round(self.quantity_kg, 2),
            "quantity_quintals": round(self.quantity_quintals, 2),
            "quantity_tonnes": round(self.quantity_tonnes, 3),
            "grade_a_kg": round(self.grade_a_kg, 2),
            "urs_kg": round(self.urs_kg, 2),
            "rejected_kg": round(self.rejected_kg, 2),
            "current_balance_kg": round(self.current_balance_kg, 2),
            "grade_a_balance_kg": round(self.grade_a_balance_kg, 2),
            "urs_balance_kg": round(self.urs_balance_kg, 2),
            "rejected_balance_kg": round(self.rejected_balance_kg, 2),
            "has_physical_quantity": self.quantity_kg > 0,
            "total_onions": self.total_onions,
            "grade_a_count": self.grade_a_count,
            "urs_count": self.urs_count,
            "rejected_count": self.rejected_count,
            "primary_category": self.primary_category,
            "status": self.status,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class InventoryMovement(db.Model):
    __tablename__ = "inventory_movements"

    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id = db.Column(db.String(60), nullable=False, index=True)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    movement_type = db.Column(db.String(30), nullable=False)  # IN, OUT_SALE, OUT_DISPATCH, SPOILAGE_DISCARD
    category = db.Column(db.String(30), default="Consolidated")  # Grade A, URS, Rejected, Consolidated
    quantity_in = db.Column(db.Float, default=0.0, nullable=False)
    quantity_out = db.Column(db.Float, default=0.0, nullable=False)
    balance = db.Column(db.Float, default=0.0, nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    destination = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    inventory_item = db.relationship("InventoryItem", back_populates="movements")

    def to_dict(self):
        return {
            "id": self.id,
            "movement_id": self.id,
            "inventory_id": self.inventory_id,
            "batch_id": self.batch_id,
            "date": self.date.strftime("%d/%m/%Y %I:%M %p") if self.date else None,
            "movement_type": self.movement_type,
            "category": self.category,
            "quantity_in": round(self.quantity_in, 2),
            "quantity_out": round(self.quantity_out, 2),
            "balance": round(self.balance, 2),
            "reason": self.reason,
            "destination": self.destination,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class InventorySetting(db.Model):
    __tablename__ = "inventory_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(60), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @staticmethod
    def get_setting(key, default_val):
        setting = InventorySetting.query.filter_by(key=key).first()
        return setting.value if setting else default_val

    @staticmethod
    def set_setting(key, value, description=None):
        setting = InventorySetting.query.filter_by(key=key).first()
        if not setting:
            setting = InventorySetting(key=key, value=str(value), description=description)
            db.session.add(setting)
        else:
            setting.value = str(value)
            if description:
                setting.description = description
        db.session.commit()
        return setting
