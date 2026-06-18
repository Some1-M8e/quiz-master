from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import RSVP
from email_service import send_rsvp_confirmation

router = APIRouter(prefix="/rsvp", tags=["rsvps"])


class RSVPUpdate(BaseModel):
    companions: int = 0


@router.get("/{token}/{response}")
def rsvp_via_link(token: str, response: str, companions: int = 0, db: Session = Depends(get_db)):
    if response not in ("yes", "no", "maybe"):
        raise HTTPException(400, "Ungültige Antwort")
    rsvp = db.query(RSVP).filter_by(token=token).first()
    if not rsvp:
        raise HTTPException(404, "Link ungültig")
    rsvp.response = response
    if response == "yes":
        rsvp.companions = max(0, companions)
    db.commit()
    if response in ("yes", "maybe") and rsvp.participant.notifications_enabled and rsvp.participant.email:
        send_rsvp_confirmation(
            participant_name=rsvp.participant.name,
            email=rsvp.participant.email,
            event_title=rsvp.event.title,
            event_date=rsvp.event.event_date.strftime("%d.%m.%Y"),
            event_description=rsvp.event.description or "",
            response=response,
        )
    return {"message": "Antwort gespeichert", "response": response}


@router.get("/{token}")
def rsvp_page_data(token: str, db: Session = Depends(get_db)):
    rsvp = db.query(RSVP).filter_by(token=token).first()
    if not rsvp:
        raise HTTPException(404)
    return {
        "participant_name": rsvp.participant.name,
        "participant_email": rsvp.participant.email,
        "event_title": rsvp.event.title,
        "event_date": rsvp.event.event_date.strftime("%d.%m.%Y"),
        "current_response": rsvp.response,
        "companions": rsvp.companions,
        "detail_url": rsvp.event.detail_url,
        "token": token,
    }


@router.put("/{rsvp_id}")
def edit_rsvp(rsvp_id: int, response: str, companions: int = 0, db: Session = Depends(get_db)):
    rsvp = db.get(RSVP, rsvp_id)
    if not rsvp:
        raise HTTPException(404)
    if response not in ("yes", "no", "maybe", None):
        raise HTTPException(400, "Ungültige Antwort")
    rsvp.response = response
    if response == "yes":
        rsvp.companions = max(0, companions)
    db.commit()
    return {"message": "RSVP aktualisiert"}
