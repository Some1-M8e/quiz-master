import asyncio
import logging
import httpx
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from models import Provider, Event
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


def _extract_detail_url(event_el, provider_url: str) -> str | None:
    """Ermittelt den Link zur Event-Detailseite aus dem Squarespace-HTML."""
    href = None

    # 1. "Veranstaltung ansehen"-Button (eventlist-button)
    btn = event_el.find(class_=lambda c: c and "eventlist-button" in c)
    if btn:
        a = btn if btn.name == "a" else btn.find("a")
        if a:
            href = a.get("href")

    # 2. Titel-Link als Fallback
    if not href:
        title = event_el.find(class_=lambda c: c and "eventlist-title" in c)
        if title:
            a = title.find("a")
            if a:
                href = a.get("href")

    if not href:
        return None

    if href.startswith("http"):
        return href
    return urljoin(provider_url, href)


def scrape_provider(provider: Provider, db: Session) -> list[dict]:
    try:
        response = httpx.get(provider.url, timeout=10, follow_redirects=True)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Fehler beim Abrufen von {provider.url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    found_events = []

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    booking_window = today + timedelta(days=30)

    for event_el in soup.find_all(class_=lambda c: c and "eventlist-event--upcoming" in c):
        time_el = event_el.find("time", class_="event-date")
        title_el = event_el.find(class_="eventlist-title")
        status_el = event_el.find(class_="eventlist-datetag-status")

        if not time_el or not time_el.get("datetime"):
            continue

        try:
            date = datetime.strptime(time_el["datetime"], "%Y-%m-%d")
        except ValueError:
            continue

        status = status_el.get_text(strip=True).lower() if status_el else ""
        if any(word in status for word in ["ausverkauft", "abgesagt", "sold out", "cancelled"]):
            continue

        # Pension Schmidt öffnet Reservierungen erst 30 Tage vorher
        if date > booking_window:
            continue

        title = title_el.get_text(strip=True) if title_el else time_el.get_text(strip=True)

        # Nur bekannte Quiz-Typen verarbeiten
        from email_service import _quiz_category
        if not _quiz_category(title):
            logger.info(f"Event '{title}' ist kein bekannter Quiz-Typ — übersprungen")
            continue

        desc_el = event_el.find(class_=lambda c: c and (
            "eventlist-description" in c or "eventlist-excerpt" in c
        ))
        description = desc_el.get_text(" ", strip=True) if desc_el else ""

        # Nur eintragen wenn noch nicht vorhanden
        existing = db.query(Event).filter_by(provider_id=provider.id, event_date=date).first()
        if existing:
            continue

        detail_url = _extract_detail_url(event_el, provider.url)
        if not detail_url:
            logger.warning(f"Kein Detail-Link für Event am {date.strftime('%d.%m.%Y')} — übersprungen")
            continue

        # Buchbarkeitsprüfung: Sind 19:00–19:30 Plätze für 4 Personen frei?
        from booking import check_bookable
        try:
            is_bookable = asyncio.run(check_bookable(detail_url, date))
        except Exception as e:
            logger.error(f"Buchbarkeitsprüfung fehlgeschlagen ({detail_url}): {e}")
            continue

        if not is_bookable:
            logger.info(f"Event am {date.strftime('%d.%m.%Y')} nicht buchbar — übersprungen")
            continue

        found_events.append({"title": title, "date": date, "detail_url": detail_url, "description": description})

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
                detail_url=ev["detail_url"],
                description=ev.get("description") or None,
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
                    event_description=event.description or "",
                )
            db.commit()
            logger.info(f"Neuer Termin gefunden und Einladungen versandt: {event.title}")
