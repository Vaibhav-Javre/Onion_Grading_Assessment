import json
from flask import has_request_context, request, session

from backend.database.db import db
from backend.models.audit import AuditLog


def record_audit_log(action: str, entity_type: str, entity_id: str | None = None, details: dict | str | None = None, user=None):
    """
    Records an immutable audit event in the database.
    Can be called inside or outside HTTP request contexts safely.
    """
    try:
        actor_user_id = None
        actor_name = "System Automated"
        actor_role = "system"
        ip_address = "127.0.0.1"
        user_agent = "System"

        if user:
            actor_user_id = getattr(user, "id", None)
            actor_name = getattr(user, "name", "User")
            actor_role = getattr(user, "role", "user")

        if has_request_context():
            if not user and "user_id" in session:
                actor_user_id = session.get("user_id")
                actor_name = session.get("user_name", "Authenticated User")
                actor_role = session.get("user_role", "user")

            # Extract client IP
            if request.headers.get("X-Forwarded-For"):
                ip_address = request.headers.get("X-Forwarded-For").split(",")[0].strip()
            elif request.remote_addr:
                ip_address = request.remote_addr

            user_agent = request.headers.get("User-Agent", "")[:250]

        details_str = None
        if details is not None:
            if isinstance(details, (dict, list)):
                try:
                    details_str = json.dumps(details)
                except Exception:
                    details_str = str(details)
            else:
                details_str = str(details)

        log_entry = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            actor_user_id=actor_user_id,
            actor_name=actor_name,
            actor_role=actor_role,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details_str
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry
    except Exception as e:
        db.session.rollback()
        print(f"[AuditHelper Warning] Failed to log audit action '{action}': {e}")
        return None
