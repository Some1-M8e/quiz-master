import asyncio
import logging
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from database import SessionLocal
from models import Event, RSVP

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()

MIN_PARTICIPANTS = 4  # Mindestanzahl f체r Buchungserhalt (7 Tage vor Event)
BOOKING_DEADLINE_DAYS = 4
CANCELLATION_DAYS_BEFORE = 7
CAPACITY = 5  # Buchung erfolgt sofort f체r 5 Personen
ENABLE_4DAY_RULE = False

def _total_attendees(event: Event, include_maybe: bool = True) -> int:
    now = datetime.now(timezone.utc)
    event_date = event.event_date.replace(tzinfo=timezone.utc) if event.event_date.tzinfo is None else event.event_date
    days_until = (event_date - now).days

    valid_responses = ["yes"]
    if include_maybe and days_until > 7:
        valid_responses.append("maybe")

    rsvps = [r for r in event.rsvps if r.response in valid_responses]
    return sum(1 + r.companions for r in rsvps)

def _select_lineup(event: Event) -> None:
    now = datetime.now(timezone.utc)
    event_date = event.event_date.replace(tzinfo=timezone.utc) if event.event_date.tzinfo is None else event.event_date
    days_until = (event_date - now).days

    rsvps = sorted(event.rsvps, key=lambda r: r.created_at)

    capacity_left = CAPACITY
    for rsvp in rsvps:
        if rsvp.response not in ("yes", "maybe"):
            rsvp.selected = False
            continue

        if rsvp.response == "maybe" and days_until <= 7:
            rsvp.selected = False
            continue

        persons_needed = 1 + rsvp.companions
        if capacity_left >= persons_needed:
            rsvp.selected = True
            capacity_left -= persons_needed
        else:
            rsvp.selected = False

def job_scraper():
    from scraper import run_scraper
    from datetime import datetime, timezone
    db = SessionLocal()
    try:
        run_scraper(db)
        # Lasten-Update speichern
        from models import Setting
        existing = db.query(Setting).filter_by(key="last_scraper_run").first()
        if existing:
            existing.value = datetime.now(timezone.utc).isoformat()
        else:
            db.add(Setting(key="last_scraper_run", value=datetime.now(timezone.utc).isoformat()))
        db.commit()
    finally:
        db.close()

def job_booking_logic():
    from email_service import send_booking_confirmation, send_cancellation, send_booking_warning, send_maybe_reminder
    import booking as booking_module

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        booked_events = db.query(Event).filter_by(status="gebucht").all()
        for event in booked_events:
            event_date = event.event_date.replace(tzinfo=timezone.utc) if event.event_date.tzinfo is None else event.event_date
            days_until = (event_date - now).days

            yes_count = sum(1 + r.companions for r in event.rsvps if r.response == "yes")
            maybe_count = sum(1 + r.companions for r in event.rsvps if r.response == "maybe")

            # --- 7 Tage vor Event: Erste Prüfung ---
            if days_until == 7:
                total_positive = yes_count + maybe_count  # Ja + Vielleicht zusammen

                if total_positive < MIN_PARTICIPANTS:
                    # Zu wenige positive Antworten insgesamt (Ja + Maybe) — sofort stornieren
                    logger.info(f"Event {event.title}: Nur {total_positive} positive Antworten (Ja+Maybe, benötigt {MIN_PARTICIPANTS}) → Sofortige Stornierung")
                    success = asyncio.run(booking_module.cancel_booking(
                        detail_url=event.detail_url or event.provider.url,
                        event_date=event.event_date,
                        event_title=event.title,
                    ))
                    if success:
                        event.status = "cancelled"
                        db.commit()
                        for rsvp in event.rsvps:
                            if rsvp.participant.notifications_enabled and rsvp.participant.email:
                                send_cancellation(
                                    rsvp.participant.name, rsvp.participant.email,
                                    event.title, event.event_date.strftime("%d.%m.%Y"),
                                    event_description=event.description or ""
                                )
                        logger.info(f"Termin storniert: {event.title}")
                elif yes_count >= MIN_PARTICIPANTS:
                    # Genug feste Zusagen — Buchung bleibt, Maybe-Erinnerung senden
                    logger.info(f"Event {event.title}: {yes_count} Ja-Stimmen → Buchung bestätigt, Maybe-Erinnerung gesendet")
                    for rsvp in event.rsvps:
                        if rsvp.response in ("yes", "maybe") and rsvp.participant.notifications_enabled and rsvp.participant.email:
                            send_booking_confirmation(
                                rsvp.participant.name, rsvp.participant.email,
                                event.title, event.event_date.strftime("%d.%m.%Y"),
                                event_description=event.description or "",
                                response=rsvp.response
                            )
                    # Maybe-Teilnehmer erhalten Erinnerung mit 48h Frist (nur wenn noch nicht gesendet)
                    for rsvp in event.rsvps:
                        if rsvp.response == "maybe" and rsvp.reminder_sent_at is None and rsvp.participant.notifications_enabled and rsvp.participant.email:
                            send_maybe_reminder(
                                rsvp.participant.name, rsvp.participant.email,
                                event.title, event.event_date.strftime("%d.%m.%Y"),
                                rsvp.token, event_description=event.description or ""
                            )
                            rsvp.reminder_sent_at = now
                    db.commit()
                    # Warn-E-Mail an Ja-Teilnehmer wenn Maybe kritisch sind
                    if maybe_count > 0:
                        send_booking_warning(
                            event_title=event.title,
                            event_date=event.event_date.strftime("%d.%m.%Y"),
                            yes_count=yes_count,
                            maybe_count=maybe_count,
                            participants=[r.participant for r in event.rsvps if r.response == "yes" and r.participant.notifications_enabled and r.participant.email]
                        )
                else:
                    # Ja < 4 aber Ja+Maybe >= 4 — Buchung bleibt vorläufig, auf Maybe warten
                    logger.info(f"Event {event.title}: {yes_count} Ja + {maybe_count} Maybe = {total_positive} (benötigt {MIN_PARTICIPANTS}) → Warte auf Maybe-Entscheidung")

            # --- 5 Tage vor Event (48h nach Maybe-Erinnerung): Finale Prüfung ---
            elif days_until == 5:
                # Maybe automatisch zu Nein umwandeln
                for rsvp in event.rsvps:
                    if rsvp.response == "maybe":
                        rsvp.response = "no"
                db.commit()
                logger.info(f"Event {event.title}: Maybe-Stimmen automatisch zu Nein konvertiert")

                # Finale Prüfung nach Umwandlung
                yes_count = sum(1 + r.companions for r in event.rsvps if r.response == "yes")

                if yes_count >= MIN_PARTICIPANTS:
                    logger.info(f"Event {event.title}: {yes_count} Ja-Stimmen nach Maybe-Konvertierung → Buchung bleibt bestehen")
                else:
                    # Zu wenige nach Maybe-Konvertierung — stornieren
                    logger.info(f"Event {event.title}: Nur {yes_count} Ja-Stimmen nach Maybe-Konvertierung → Finale Stornierung")
                    success = asyncio.run(booking_module.cancel_booking(
                        detail_url=event.detail_url or event.provider.url,
                        event_date=event.event_date,
                        event_title=event.title,
                    ))
                    if success:
                        event.status = "cancelled"
                        db.commit()
                        for rsvp in event.rsvps:
                            if rsvp.participant.notifications_enabled and rsvp.participant.email:
                                send_cancellation(
                                    rsvp.participant.name, rsvp.participant.email,
                                    event.title, event.event_date.strftime("%d.%m.%Y"),
                                    event_description=event.description or ""
                                )
                        logger.info(f"Termin storniert: {event.title}")

    finally:
        db.close()

def job_reminders():
    from email_service import send_reminder
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        booked_events = db.query(Event).filter_by(status="gebucht").all()
        for event in booked_events:
            event_date = event.event_date.replace(tzinfo=timezone.utc) if event.event_date.tzinfo is None else event.event_date
            days_until = (event_date - now).days
            if days_until == 1:
                for rsvp in event.rsvps:
                    if rsvp.response == "yes" and rsvp.participant.notifications_enabled and rsvp.participant.email:
                        send_reminder(rsvp.participant.name, rsvp.participant.email, event.title, event.event_date.strftime("%d.%m.%Y"), event_description=event.description or "")
    finally:
        db.close()

def job_maybe_reminders():
    # Diese Funktion wurde in job_booking_logic integriert (Tag 7 Prüfung)
    # Hier nur noch als Platzhalter für Kompatibilität
    pass

def job_maybe_auto_convert():
    # Diese Funktion wurde in job_booking_logic integriert (Tag 5 Prüfung)
    # Hier nur noch als Platzhalter für Kompatibilität
    pass

def job_weekly_reminder():
    from email_service import send_weekly_reminder
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        booked_events = db.query(Event).filter_by(status="gebucht").all()
        for event in booked_events:
            for rsvp in event.rsvps:
                if rsvp.response in (None, "maybe") and rsvp.response != "no" and rsvp.participant.notifications_enabled and rsvp.participant.email:
                    send_weekly_reminder(rsvp.participant.name, rsvp.participant.email, event.title, event.event_date.strftime("%d.%m.%Y"), rsvp.token, event_description=event.description or "")
        db.commit()
    finally:
        db.close()

def start_scheduler():
    scheduler.add_job(job_scraper, "interval", hours=2, id="scraper")
    scheduler.add_job(job_booking_logic, "interval", hours=1, id="booking")
    # job_maybe_reminders und job_maybe_auto_convert sind deaktiviert (in job_booking_logic integriert)
    scheduler.add_job(job_reminders, "cron", hour=8, minute=0, id="reminders")
    scheduler.add_job(job_weekly_reminder, "cron", day_of_week=3, hour=8, minute=0, id="weekly_reminder")
    scheduler.start()
    logger.info("Scheduler gestartet.")

def stop_scheduler():
    scheduler.shutdown()
