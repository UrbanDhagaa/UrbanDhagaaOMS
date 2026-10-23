from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.operations import AuditLog


async def record_audit_log(
    db: AsyncSession,
    actor: str,
    action: str,
    entity_name: str,
    entity_id: str,
    before_state: Optional[dict] = None,
    after_state: Optional[dict] = None,
    notes: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    log = AuditLog(
        actor=actor,
        action=action,
        entity_name=entity_name,
        entity_id=str(entity_id),
        before_state=before_state,
        after_state=after_state,
        notes=notes,
        ip_address=ip_address,
    )
    db.add(log)
    return log
