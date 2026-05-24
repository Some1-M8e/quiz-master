import logging
import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from models import Provider, Event
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def scrape_provider(provider: Provider, db: Session) -> list[dict]:
    """Lädt die Provider-Seite und sucht nach Terminen. Gibt neue Termine zurück."""
    try:
        response = httpx.get(provider.url, timeout=10, follow_redirects=True)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Fehler beim Abrufen von {provider.url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    # Generische Erkennung — muss je nach Anbieter-Website angepasst werden
    # Sucht nach Datumsangaben in gängigen Mustern
    found_events = []
    for tag in soup.find_all(["time", "span", "div", "p"]):
        text = tag.get_text(strip=True)
        for fmt in ["%d.%m.%Y", "%Y-%m-%d", "%d. %B %Y"]:
            try:
                date = datetime.strptime(text[:len(fmt)+2].strip(), fmt)
                title = tag.find_parent().get_text(strip=True)[:100] if tag.find_parent() else text
                existing = db.query(Event).filter_by(provider_id=provider.id, event_date=date).first()
                if not existing:
                    found_events.append({"title": title, "date": date})
                break
            except ValueError:
                continue
    return found_events

def run_scraper(db: Session):
    from email_service import send_invitation
    from models import Participant, RSVP

    providers = db.query(Provider).all()
    for provider in providers:
        logger.info(f"Prüfe Anbieter: {provider.name} ({provider.url})")
        new_events = scrape_provider(provider, db)
        for ev in new_events:
            event = Event(
                provider_id=provider.id,
                title=ev["title"],
                event_date=ev["date"],
                status="pending",
                created_at=datetime.now(timezone.utc),
            )
            db.add(event)
            db.flush()
            participants = db.query(Participant).all()
            for p in participants:
                rsvp = RSVP(event_id=event.id, participant_id=p.id)
                db.add(rsvp)
                db.flush()
                send_invitation(
                    participant_name=p.name,
                    email=p.email,
                    event_title=event.title,
                    event_date=event.event_date.strftime("%d.%m.%Y"),
                    token=rsvp.token,
                )
            db.commit()
            logger.info(f"Neuer Termin gefunden und Einladungen versandt: {event.title}")
