from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def create_audit_log(
    db: Session,
    event: str,
    resource_type: str,
    resource_id: int | None = None,
    user_id: int | None = None,
    details: dict | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        user_id=user_id,
        event=event,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log