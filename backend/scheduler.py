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
CAPACITY = 5

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
                    event.capacity = CAPACITY
                    _select_lineup(event)
                    db.commit()
                    for rsvp in event.rsvps:
                        if rsvp.response == "yes" and rsvp.selected:
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

def job_maybe_reminders():
    from email_service import send_maybe_reminder
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        booked_events = db.query(Event).filter_by(status="booked").all()
        for event in booked_events:
            event_date = event.event_date.replace(tzinfo=timezone.utc) if event.event_date.tzinfo is None else event.event_date
            days_until = (event_date - now).days

            if days_until == 7:
                for rsvp in event.rsvps:
                    if rsvp.response == "maybe" and rsvp.reminder_sent_at is None:
                        send_maybe_reminder(rsvp.participant.name, rsvp.participant.email, event.title, event.event_date.strftime("%d.%m.%Y"), rsvp.token, event_description=event.description or "")
                        rsvp.reminder_sent_at = now
                db.commit()
    finally:
        db.close()

def job_maybe_auto_convert():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        all_events = db.query(Event).all()
        for event in all_events:
            for rsvp in event.rsvps:
                if rsvp.response == "maybe" and rsvp.reminder_sent_at is not None:
                    time_since_reminder = now - rsvp.reminder_sent_at
                    if time_since_reminder >= timedelta(hours=24):
                        rsvp.response = "no"
                        logger.info(f"Participant {rsvp.participant.name}: 'maybe' zu 'no' konvertiert (24h Frist abgelaufen)")
        db.commit()
    finally:
        db.close()

def start_scheduler():
    scheduler.add_job(job_scraper, "interval", hours=1, id="scraper")
    scheduler.add_job(job_booking_logic, "interval", hours=1, id="booking")
    scheduler.add_job(job_maybe_reminders, "interval", hours=1, id="maybe_reminders")
    scheduler.add_job(job_maybe_auto_convert, "interval", hours=1, id="maybe_auto_convert")
    scheduler.add_job(job_reminders, "cron", hour=8, minute=0, id="reminders")
    scheduler.start()
    logger.info("Scheduler gestartet.")

def stop_scheduler():
    scheduler.shutdown()
