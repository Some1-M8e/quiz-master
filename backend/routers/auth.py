from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from config import settings
from sqlalchemy.orm import Session
from database import get_db
from models import Participant
from email_service import send_participant_welcome
from fastapi import Depends
import urllib.parse

router = APIRouter(tags=["auth"])


class ParticipantCreate(BaseModel):
    name: str
    email: str


@router.get("/admin/invite")
def get_invite_link():
    return {"token": settings.invite_token}


@router.get("/invite/{token}")
def validate_invite(token: str):
    if token != settings.invite_token:
        raise HTTPException(404, "Link ungültig")
    return {"valid": True}


@router.post("/invite/{token}", status_code=201)
def register_via_invite(token: str, body: ParticipantCreate, db: Session = Depends(get_db)):
    if token != settings.invite_token:
        raise HTTPException(404, "Link ungültig oder abgelaufen")
    existing = db.query(Participant).filter_by(email=body.email).first()
    if existing:
        raise HTTPException(409, "E-Mail bereits registriert")
    participant = Participant(name=body.name, email=body.email)
    db.add(participant)
    db.commit()
    db.refresh(participant)
    send_participant_welcome(participant.name, participant.email)
    return {"message": "Erfolgreich registriert", "name": participant.name}


@router.get("/unsubscribe/{email}")
def unsubscribe(email: str, db: Session = Depends(get_db)):
    decoded_email = urllib.parse.unquote(email)
    participant = db.query(Participant).filter_by(email=decoded_email).first()
    if not participant:
        return {"message": "Teilnehmer nicht gefunden"}
    participant.notifications_enabled = False
    db.commit()
    return {"message": "Benachrichtigungen erfolgreich abbestellt. Du erhältst keine weiteren E-Mails."}


@router.get("/settings/last-scraper-run")
def get_last_scraper_run(db: Session = Depends(get_db)):
    from models import Setting
    from datetime import datetime

    s = db.query(Setting).filter_by(key="last_scraper_run").first()
    if s and s.value:
        try:
            dt = datetime.fromisoformat(s.value.replace("Z", "+00:00"))
            return {"last_run": dt.strftime("%d.%m.%Y %H:%M Uhr")}
        except Exception:
            pass
    return {"last_run": "noch nicht"}
