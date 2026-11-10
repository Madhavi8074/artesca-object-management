from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent


def create_audit_event(
    db: Session,
    action: str,
    object_id: int | None = None,
    user_id: int | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    source_ip: str | None = None,
    success: bool = True,
    error_code: str | None = None,
    details: dict | None = None,
):
    event = AuditEvent(
        user_id=user_id,
        action=action,
        object_id=object_id,
        resource_type=resource_type,
        resource_id=resource_id,
        source_ip=source_ip,
        success=success,
        error_code=error_code,
        details=details,
    )

    db.add(event)

    return event
