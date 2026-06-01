import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db, init_db
from models import Provider, Event, Participant, RSVP
from email_service import send_rsvp_confirmation, send_participant_welcome, send_participant_removed

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Quiz-Master", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://localhost:5174"], allow_methods=["*"], allow_headers=["*"])

# --- Schemas ---

class ProviderCreate(BaseModel):
    name: str
    url: str

class ParticipantCreate(BaseModel):
    name: str
    email: str

class RSVPUpdate(BaseModel):
    companions: int = 0

# --- Provider ---

@app.get("/providers")
def list_providers(db: Session = Depends(get_db)):
    return db.query(Provider).all()

@app.post("/providers", status_code=201)
def create_provider(body: ProviderCreate, db: Session = Depends(get_db)):
    provider = Provider(name=body.name, url=body.url)
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider

@app.delete("/providers/{provider_id}", status_code=204)
def delete_provider(provider_id: int, db: Session = Depends(get_db)):
    provider = db.get(Provider, provider_id)
    if not provider:
        raise HTTPException(404)
    db.delete(provider)
    db.commit()

# --- Participants ---

@app.get("/participants")
def list_participants(db: Session = Depends(get_db)):
    return db.query(Participant).all()

@app.post("/participants", status_code=201)
def create_participant(body: ParticipantCreate, db: Session = Depends(get_db)):
    participant = Participant(name=body.name, email=body.email)
    db.add(participant)
    db.commit()
    db.refresh(participant)
    send_participant_welcome(participant.name, participant.email)
    return participant

@app.delete("/participants/{participant_id}", status_code=204)
def delete_participant(participant_id: int, db: Session = Depends(get_db)):
    participant = db.get(Participant, participant_id)
    if not participant:
        raise HTTPException(404)
    name, email = participant.name, participant.email
    db.delete(participant)
    db.commit()
    send_participant_removed(name, email)

# --- Events ---

@app.get("/events")
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

@app.get("/events/{event_id}")
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

# --- RSVP via E-Mail-Link ---

@app.get("/rsvp/{token}/{response}")
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
    if response in ("yes", "maybe"):
        send_rsvp_confirmation(
            participant_name=rsvp.participant.name,
            email=rsvp.participant.email,
            event_title=rsvp.event.title,
            event_date=rsvp.event.event_date.strftime("%d.%m.%Y"),
            event_description=rsvp.event.description or "",
            response=response,
        )
    return {"message": "Antwort gespeichert", "response": response}

@app.get("/rsvp/{token}")
def rsvp_page_data(token: str, db: Session = Depends(get_db)):
    rsvp = db.query(RSVP).filter_by(token=token).first()
    if not rsvp:
        raise HTTPException(404)
    return {
        "participant_name": rsvp.participant.name,
        "event_title": rsvp.event.title,
        "event_date": rsvp.event.event_date.strftime("%d.%m.%Y"),
        "current_response": rsvp.response,
        "companions": rsvp.companions,
        "token": token,
    }

# --- Scheduler manuell steuern ---

@app.post("/admin/scraper/run", status_code=200)
def run_scraper_now(db: Session = Depends(get_db)):
    from scraper import run_scraper
    run_scraper(db)
    return {"message": "Scraper ausgeführt"}

@app.post("/admin/booking/run", status_code=200)
def run_booking_now():
    from scheduler import job_booking_logic
    job_booking_logic()
    return {"message": "Buchungslogik ausgeführt"}

@app.post("/admin/scheduler/start", status_code=200)
def start_scheduler():
    from scheduler import start_scheduler as _start
    _start()
    return {"message": "Scheduler gestartet"}
