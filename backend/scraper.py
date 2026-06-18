import logging
import asyncio
import httpx
import unicodedata
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from models import Provider, Event
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


def _normalize_title(text: str) -> str:
    """Normalisiert Titel: Umlaute, Groß/Klein, Whitespace."""
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.lower().strip()


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
        # Keine Events überspringen - alle anzeigen

        # Pension Schmidt öffnet Reservierungen erst 30 Tage vorher
        if date > booking_window:
            continue

        title = title_el.get_text(strip=True) if title_el else time_el.get_text(strip=True)

        target_titles = (
            "Quiz Quiz Bang Bang",
            "VerQUIZmeinnicht",
            "Wer wird Pensionär?",
            "VerQUIZmeinNerd",
        )

        title_normalized = _normalize_title(title)
        target_normalized = [_normalize_title(t) for t in target_titles]

        if title_normalized not in target_normalized:
            logger.info(f"Event '{title}' wird ignoriert — nicht im Ziel-Filter")
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

        # Buchbarkeitsprüfung: prüfe wie viele Plätze verfügbar sind (2-4)
        try:
            from booking import check_partial_bookable
            available_slots = asyncio.run(check_partial_bookable(detail_url, date))
        except ImportError:
            logger.info(f"Booking-Modul nicht verfügbar — nutze Standard: 4 Plätze")
            available_slots = 4
        except Exception as e:
            logger.info(f"Buchbarkeitsprüfung übersprungen ({e}) — nutze Standard: 4 Plätze")
            available_slots = 4

        # Status basierend auf Website-Status UND verfügbarer Kapazität
        # Nur "pending" = buchbar mit 4+ Slots wird sofort gebucht
        if any(word in status for word in ["abgesagt", "cancelled"]):
            event_status = "cancelled"
        elif any(word in status for word in ["ausverkauft", "sold out"]) or available_slots == 0:
            event_status = "ausverkauft"
        elif available_slots < 4:
            event_status = "teilweise_ausverkauft"  # 2-3 Plätze → wird nicht gebucht
        else:
            event_status = "pending"  # 4+ Plätze → wird SOFORT gebucht

        logger.info(f"Event '{title}' am {date.strftime('%d.%m.')}: {available_slots} Plätze verfügbar → {event_status}")
        found_events.append({"title": title, "date": date, "detail_url": detail_url, "description": description, "status": event_status})

    return found_events


def _is_excluded_from_booking(title: str) -> bool:
    """Prüft ob ein Event von der automatischen Buchung ausgeschlossen ist."""
    t = _normalize_title(title)
    return "wer wird pensionar" in t


def run_scraper(db: Session):
    from email_service import send_invitation, send_event_found_notification
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
                status=ev["status"],
                created_at=datetime.now(timezone.utc),
            )
            db.add(event)
            db.flush()

            # Prüfen ob Event von Buchung ausgeschlossen ist (z.B. "Wer wird Pensionär?")
            is_excluded = _is_excluded_from_booking(ev["title"])

            if ev["status"] == "pending":
                if is_excluded:
                    # Nur Info-Mail versenden, NICHT buchen
                    event.status = "pending"  # Bleibt pending, wird nicht gebucht
                    db.commit()
                    logger.info(f"Event '{ev['title']}' am {ev['date'].strftime('%d.%m.')} - Info-Mail versendet (keine automatische Buchung)")

                    participants = db.query(Participant).filter_by(notifications_enabled=True).all()
                    for p in participants:
                        if not p.email:
                            continue
                        send_event_found_notification(
                            participant_name=p.name,
                            email=p.email,
                            event_title=event.title,
                            event_date=event.event_date.strftime("%d.%m.%Y"),
                            event_description=event.description or "",
                            detail_url=event.detail_url,
                        )
                    logger.info(f"Info-Mails versandt für Event {event.id}")
                else:
                    # Normale Buchung für 5 Personen
                    import asyncio
                    from booking import book_event
                    success = asyncio.run(book_event(ev["detail_url"], ev["date"], ev["title"]))
                    if success:
                        event.status = "booked"
                        event.capacity = 5
                        db.commit()
                        logger.info(f"Event '{ev['title']}' am {ev['date'].strftime('%d.%m.')} SOFORT gebucht für 5 Personen")

                        participants = db.query(Participant).filter_by(notifications_enabled=True).all()
                        for p in participants:
                            if not p.email:
                                continue
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
                        logger.info(f"Einladungen versandt für Event {event.id}")
                    else:
                        db.commit()
                        logger.warning(f"Event '{ev['title']}' am {ev['date'].strftime('%d.%m.')} NICHT gebucht (Buchung fehlgeschlagen) - manuell prüfen!")
            else:
                # Event war ausverkauft/abgesagt — nur eintragen ohne Buchung
                event.status = ev["status"]
                db.commit()
                logger.info(f"Event '{ev['title']}' nicht gebucht (Status: {ev['status']})")
