from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.models.audit_event import AuditEvent
from app.models.user import User
from app.services.permissions import require_permission


router = APIRouter(
    prefix="/api/v1/audit",
    tags=["Audit"],
    dependencies=[Depends(get_current_user), Depends(require_permission("AUDIT_READ"))],
)


@router.get("/")
def list_audit_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    events = (
        db.query(AuditEvent, User.username)
        .outerjoin(User, User.id == AuditEvent.user_id)
        .order_by(AuditEvent.timestamp.desc())
        .limit(200)
        .all()
    )

    return [
        {
            "id": event.id,
            "action": event.action,
            "object_id": event.object_id,
            "user_id": event.user_id,
            "username": username or (f"User #{event.user_id}" if event.user_id else "System"),
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "success": event.success,
            "error_code": event.error_code,
            "details": event.details,
            "timestamp": event.timestamp,
        }
        for event, username in events
    ]


@router.get("/object/{object_id}")
def list_object_audit_events(
    object_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    events = (
        db.query(AuditEvent, User.username)
        .outerjoin(User, User.id == AuditEvent.user_id)
        .filter(AuditEvent.object_id == object_id)
        .order_by(AuditEvent.timestamp.desc())
        .all()
    )

    return [
        {
            "id": event.id,
            "action": event.action,
            "object_id": event.object_id,
            "user_id": event.user_id,
            "username": username or (f"User #{event.user_id}" if event.user_id else "System"),
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "success": event.success,
            "error_code": event.error_code,
            "details": event.details,
            "timestamp": event.timestamp,
        }
        for event, username in events
    ]