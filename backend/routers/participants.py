from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import Participant
from email_service import send_participant_welcome, send_participant_removed

router = APIRouter(prefix="/participants", tags=["participants"])


class ParticipantCreate(BaseModel):
    name: str
    email: str | None = None


@router.get("")
def list_participants(db: Session = Depends(get_db)):
    return db.query(Participant).all()


@router.post("", status_code=201)
def create_participant(body: ParticipantCreate, db: Session = Depends(get_db)):
    if body.email:
        existing = db.query(Participant).filter_by(email=body.email).first()
        if existing:
            raise HTTPException(status_code=409, detail="E-Mail-Adresse ist bereits registriert")
    participant = Participant(name=body.name, email=body.email)
    db.add(participant)
    db.commit()
    db.refresh(participant)
    if body.email:
        send_participant_welcome(participant.name, participant.email)
    return participant


@router.delete("/{participant_id}", status_code=204)
def delete_participant(participant_id: int, db: Session = Depends(get_db)):
    participant = db.get(Participant, participant_id)
    if not participant:
        raise HTTPException(404)
    name, email = participant.name, participant.email
    db.delete(participant)
    db.commit()
    send_participant_removed(name, email)
