import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db, init_db
from models import Provider, Event, Participant, RSVP, Setting
from email_service import send_rsvp_confirmation, send_participant_welcome, send_participant_removed, _send

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Scheduler im Hintergrund starten
    import threading
    from scheduler import start_scheduler
    def _start():
        start_scheduler()
    threading.Thread(target=_start, daemon=True).start()
    yield

app = FastAPI(title="Quiz-Master", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://localhost:5174"], allow_methods=["*"], allow_headers=["*"])

# --- Schemas ---

class ProviderCreate(BaseModel):
    name: str
    url: str

class ParticipantCreate(BaseModel):
    name: str
    email: str | None = None

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
    # Alle Events des Providers löschen (mit CASCADE für RSVPs)
    db.query(Event).filter_by(provider_id=provider_id).delete(synchronize_session=False)
    db.delete(provider)
    db.commit()

# --- Participants ---

@app.get("/participants")
def list_participants(db: Session = Depends(get_db)):
    return db.query(Participant).all()

@app.post("/participants", status_code=201)
def create_participant(body: ParticipantCreate, db: Session = Depends(get_db)):
    # Prüfen ob E-Mail bereits existiert (nur wenn E-Mail angegeben ist)
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

@app.get("/rsvp/{token}")
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

# --- Einladungslink (statisch) ---

INVITE_TOKEN = "quizmaster"  # Statischer Token, immer derselbe Link

@app.get("/admin/invite")
def get_invite_link(db: Session = Depends(get_db)):
    # Statische Rückgabe für Kompatibilität mit allem Code
    return {"token": INVITE_TOKEN}

@app.get("/invite/{token}")
def validate_invite(token: str, db: Session = Depends(get_db)):
    if token != INVITE_TOKEN:
        raise HTTPException(404, "Link ungültig")
    return {"valid": True}

@app.get("/unsubscribe/{email}")
def unsubscribe(email: str, db: Session = Depends(get_db)):
    import urllib.parse
    decoded_email = urllib.parse.unquote(email)
    participant = db.query(Participant).filter_by(email=decoded_email).first()
    if not participant:
        return {"message": "Teilnehmer nicht gefunden"}
    participant.notifications_enabled = False
    db.commit()
    return {"message": "Benachrichtigungen erfolgreich abbestellt. Du erhältst keine weiteren E-Mails."}

@app.get("/settings/last-scraper-run")
def get_last_scraper_run(db: Session = Depends(get_db)):
    s = db.query(Setting).filter_by(key="last_scraper_run").first()
    if s and s.value:
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(s.value.replace("Z", "+00:00"))
            return {"last_run": dt.strftime("%d.%m.%Y %H:%M Uhr")}
        except:
            pass
    return {"last_run": "noch nicht"}

@app.post("/invite/{token}", status_code=201)
def register_via_invite(token: str, body: ParticipantCreate, db: Session = Depends(get_db)):
    if token != INVITE_TOKEN:
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
def run_scraper_now(background_tasks: BackgroundTasks):
    from scraper import run_scraper
    from database import SessionLocal
    def _run():
        db = SessionLocal()
        try:
            run_scraper(db)
        finally:
            db.close()
    background_tasks.add_task(_run)
    return {"message": "Scraper gestartet"}

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


# --- Event: Manuell zum Behalten markieren ---

class ForceKeepEvent(BaseModel):
    force_keep: bool
    note: str | None = None

@app.put("/admin/events/{event_id}/force-keep")
def force_keep_event(event_id: int, body: ForceKeepEvent, db: Session = Depends(get_db)):
    """
    Event manuell zum Behalten markieren (verhindert automatische Stornierung).
    """
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

@app.get("/admin/events/{event_id}")
def get_event_admin(event_id: int, db: Session = Depends(get_db)):
    """
    Admin-View für Event mit allen Details inkl. force_keep.
    """
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
    from datetime import datetime, timezone
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
