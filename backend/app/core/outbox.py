from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.operations import OutboxEvent


async def emit_outbox_event(
    db: AsyncSession,
    event_type: str,
    payload: dict
) -> OutboxEvent:
    event = OutboxEvent(
        event_type=event_type,
        payload=payload,
        status="PENDING",
        retry_count=0
    )
    db.add(event)
    return event
