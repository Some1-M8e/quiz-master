from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import Event
from datetime import datetime, timezone

router = APIRouter(prefix="/events", tags=["events"])


class ForceKeepEvent(BaseModel):
    force_keep: bool
    note: str | None = None


@router.get("")
def list_events(db: Session = Depends(get_db)):
    events = db.query(Event).order_by(Event.event_date).all()
    result = []
    for e in events:
        yes_rsvps = [r for r in e.rsvps if r.response == "yes"]
        total = sum(1 + r.companions for r in yes_rsvps)
        result.append({
            "id": e.id,
            "title": e.title,
            "event_date": e.event_date.isoformat(),
            "status": e.status,
            "total_attendees": total,
            "rsvp_count": len(yes_rsvps),
        })
    return result


@router.get("/{event_id}")
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(404)
    rsvps = []
    for r in event.rsvps:
        rsvps.append({
            "participant_name": r.participant.name,
            "response": r.response,
            "companions": r.companions,
        })
    yes_rsvps = [r for r in event.rsvps if r.response == "yes"]
    total = sum(1 + r.companions for r in yes_rsvps)
    return {
        "id": event.id,
        "title": event.title,
        "event_date": event.event_date.isoformat(),
        "status": event.status,
        "total_attendees": total,
        "detail_url": event.detail_url,
        "rsvps": rsvps,
    }


@router.put("/{event_id}/force-keep")
def force_keep_event(event_id: int, body: ForceKeepEvent, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(404, "Event nicht gefunden")
    event.force_keep = body.force_keep
    event.force_keep_note = body.note
    db.commit()
    db.refresh(event)
    return {
        "message": f"Event {'zum Behalten markiert' if event.force_keep else 'nicht mehr zum Behalten markiert'}",
        "force_keep": event.force_keep,
        "note": event.force_keep_note,
    }


@router.get("/{event_id}/admin")
def get_event_admin(event_id: int, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(404, "Event nicht gefunden")
    rsvps = []
    for r in event.rsvps:
        rsvps.append({
            "id": r.id,
            "participant_name": r.participant.name,
            "participant_email": r.participant.email,
            "response": r.response,
            "companions": r.companions,
            "selected": r.selected,
            "token": r.token,
        })
    yes_count = sum(1 + r.companions for r in event.rsvps if r.response == "yes")
    maybe_count = sum(1 + r.companions for r in event.rsvps if r.response == "maybe")
    now = datetime.now(timezone.utc)
    event_date = event.event_date.replace(tzinfo=timezone.utc) if event.event_date.tzinfo is None else event.event_date
    days_until = (event_date - now).days
    return {
        "id": event.id,
        "title": event.title,
        "event_date": event.event_date.isoformat(),
        "status": event.status,
        "detail_url": event.detail_url,
        "description": event.description,
        "source": event.source,
        "created_at": event.created_at.isoformat(),
        "force_keep": event.force_keep,
        "force_keep_note": event.force_keep_note,
        "yes_count": yes_count,
        "maybe_count": maybe_count,
        "days_until": days_until,
        "rsvps": rsvps,
    }
