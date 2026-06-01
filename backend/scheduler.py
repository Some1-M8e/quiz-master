import asyncio
import logging
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from database import SessionLocal
from models import Event, RSVP

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()

MIN_PARTICIPANTS = 4
BOOKING_DEADLINE_DAYS = 4
CANCELLATION_DAYS_BEFORE = 7

def _total_attendees(event: Event) -> int:
    yes_rsvps = [r for r in event.rsvps if r.response == "yes"]
    return sum(1 + r.companions for r in yes_rsvps)

def job_scraper():
    from scraper import run_scraper
    db = SessionLocal()
    try:
        run_scraper(db)
    finally:
        db.close()

def job_booking_logic():
    from email_service import send_booking_confirmation, send_cancellation
    import booking as booking_module

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        pending_events = db.query(Event).filter_by(status="pending").all()
        for event in pending_events:
            total = _total_attendees(event)
            created_at = event.created_at.replace(tzinfo=timezone.utc) if event.created_at.tzinfo is None else event.created_at
            age_days = (now - created_at).days
            should_book = total >= MIN_PARTICIPANTS or age_days >= BOOKING_DEADLINE_DAYS
            if should_book:
                success = asyncio.run(booking_module.book_event(
                    detail_url=event.detail_url or event.provider.url,
                    event_date=event.event_date,
                    event_title=event.title,
                ))
                if success:
                    event.status = "booked"
                    db.commit()
                    for rsvp in event.rsvps:
                        if rsvp.response == "yes":
                            send_booking_confirmation(rsvp.participant.name, rsvp.participant.email, event.title, event.event_date.strftime("%d.%m.%Y"), event_description=event.description or "")
                    logger.info(f"Termin gebucht: {event.title}")

        booked_events = db.query(Event).filter_by(status="booked").all()
        for event in booked_events:
            event_date = event.event_date.replace(tzinfo=timezone.utc) if event.event_date.tzinfo is None else event.event_date
            days_until = (event_date - now).days
            if days_until <= CANCELLATION_DAYS_BEFORE and _total_attendees(event) < MIN_PARTICIPANTS:
                success = asyncio.run(booking_module.cancel_booking(
                    detail_url=event.detail_url or event.provider.url,
                    event_date=event.event_date,
                    event_title=event.title,
                ))
                if success:
                    event.status = "cancelled"
                    db.commit()
                    for rsvp in event.rsvps:
                        if rsvp.response == "yes":
                            send_cancellation(rsvp.participant.name, rsvp.participant.email, event.title, event.event_date.strftime("%d.%m.%Y"), event_description=event.description or "")
                    logger.info(f"Termin storniert: {event.title}")
    finally:
        db.close()

def job_reminders():
    from email_service import send_reminder
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        booked_events = db.query(Event).filter_by(status="booked").all()
        for event in booked_events:
            event_date = event.event_date.replace(tzinfo=timezone.utc) if event.event_date.tzinfo is None else event.event_date
            days_until = (event_date - now).days
            if days_until == 1:
                for rsvp in event.rsvps:
                    if rsvp.response == "yes":
                        send_reminder(rsvp.participant.name, rsvp.participant.email, event.title, event.event_date.strftime("%d.%m.%Y"), event_description=event.description or "")
    finally:
        db.close()

def start_scheduler():
    scheduler.add_job(job_scraper, "interval", hours=1, id="scraper")
    scheduler.add_job(job_booking_logic, "interval", hours=1, id="booking")
    scheduler.add_job(job_reminders, "cron", hour=8, minute=0, id="reminders")
    scheduler.start()
    logger.info("Scheduler gestartet.")

def stop_scheduler():
    scheduler.shutdown()
