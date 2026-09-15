import json
from datetime import datetime, timezone

from backend.database.db import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(80), nullable=False, index=True)        # e.g., GOVERNMENT_LOGIN, CONFIRM_EVALUATION, VIEW_REPORT, etc.
    entity_type = db.Column(db.String(50), nullable=False, index=True)   # e.g., evaluation, transaction, report, farmer, officer, auth
    entity_id = db.Column(db.String(100), nullable=True, index=True)     # e.g., ONR-2026-001089, TXN-2026-000101

    # Actor information
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_name = db.Column(db.String(120), nullable=False, default="System")
    actor_role = db.Column(db.String(50), nullable=False, default="system") # government, officer, farmer, system

    # Network / Session Context
    ip_address = db.Column(db.String(60), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    # Serialized Details / Metadata
    details = db.Column(db.Text, nullable=True)

    # Immutable timestamp
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    def to_dict(self):
        parsed_details = None
        if self.details:
            try:
                parsed_details = json.loads(self.details)
            except Exception:
                parsed_details = self.details

        return {
            "id": self.id,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id or "",
            "actor_user_id": self.actor_user_id,
            "actor_name": self.actor_name,
            "actor_role": self.actor_role,
            "ip_address": self.ip_address or "127.0.0.1",
            "user_agent": self.user_agent or "",
            "details": parsed_details,
            "timestamp": self.timestamp.strftime("%d/%m/%Y %I:%M:%S %p") if self.timestamp else "",
            "iso_timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

    def __repr__(self):
        return f"<AuditLog {self.id}: {self.action} on {self.entity_type}:{self.entity_id} by {self.actor_name}>"
