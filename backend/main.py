import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db, init_db
from models import Provider, Event, Participant, RSVP, InviteToken
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
        "detail_url": rsvp.event.detail_url,
        "token": token,
    }

# --- Einladungslink ---

@app.post("/admin/invite", status_code=201)
def generate_invite(db: Session = Depends(get_db)):
    db.query(InviteToken).delete()
    t = InviteToken()
    db.add(t)
    db.commit()
    return {"token": t.token}

@app.get("/invite/{token}")
def validate_invite(token: str, db: Session = Depends(get_db)):
    t = db.query(InviteToken).filter_by(token=token).first()
    if not t:
        raise HTTPException(404, "Link ungültig oder abgelaufen")
    return {"valid": True}

@app.post("/invite/{token}", status_code=201)
def register_via_invite(token: str, body: ParticipantCreate, db: Session = Depends(get_db)):
    t = db.query(InviteToken).filter_by(token=token).first()
    if not t:
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

# --- Events (manuell) ---

class EventCreate(BaseModel):
    title: str
    event_date: str
    capacity: int = 5
    description: str = ""
    detail_url: str = ""

@app.post("/events", status_code=201)
def create_event(body: EventCreate, db: Session = Depends(get_db)):
    from datetime import datetime as dt
    event_date = dt.fromisoformat(body.event_date)
    event = Event(
        title=body.title,
        event_date=event_date,
        capacity=body.capacity,
        description=body.description,
        detail_url=body.detail_url or None,
        status="neu",
        source="manual",
        provider_id=1
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return {"id": event.id, "title": event.title, "status": event.status}

@app.put("/events/{event_id}")
def update_event(event_id: int, body: EventCreate, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event or event.source != "manual":
        raise HTTPException(404)
    from datetime import datetime as dt
    event.title = body.title
    event.event_date = dt.fromisoformat(body.event_date)
    event.capacity = body.capacity
    event.description = body.description
    event.detail_url = body.detail_url or None
    db.commit()
    return {"message": "Event aktualisiert"}

class StatusUpdate(BaseModel):
    status: str

@app.put("/events/{event_id}/status")
def update_event_status(event_id: int, body: StatusUpdate, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event or event.source != "manual":
        raise HTTPException(404)
    if body.status not in ("neu", "gebucht", "abgesagt"):
        raise HTTPException(400, "Ungültiger Status")
    event.status = body.status
    db.commit()
    return {"message": f"Status auf '{body.status}' gesetzt"}

@app.delete("/events/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event or event.source != "manual":
        raise HTTPException(404)
    db.delete(event)
    db.commit()
    return {"message": "Event gelöscht"}

# --- RSVP (Admin-Editing) ---

@app.put("/rsvp/{rsvp_id}")
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
