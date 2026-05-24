import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings

logger = logging.getLogger(__name__)

def _send(to: str, subject: str, body_html: str):
    if settings.email_dry_run:
        logger.info(f"[DRY-RUN] E-Mail an {to} | Betreff: {subject}\n{body_html}")
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_user
    msg["To"] = to
    msg.attach(MIMEText(body_html, "html"))
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_user, to, msg.as_string())

def send_invitation(participant_name: str, email: str, event_title: str, event_date: str, token: str):
    rsvp_yes = f"{settings.app_url}/rsvp/{token}/yes"
    rsvp_no = f"{settings.app_url}/rsvp/{token}/no"
    app_link = f"{settings.app_url}/rsvp/{token}"
    body = f"""
    <p>Hallo {participant_name},</p>
    <p>es gibt einen neuen Quiz-Abend-Termin: <strong>{event_title}</strong> am <strong>{event_date}</strong>.</p>
    <p>
        <a href="{rsvp_yes}" style="padding:8px 16px;background:#22c55e;color:white;text-decoration:none;border-radius:4px;">Zusagen</a>
        &nbsp;&nbsp;
        <a href="{rsvp_no}" style="padding:8px 16px;background:#ef4444;color:white;text-decoration:none;border-radius:4px;">Absagen</a>
    </p>
    <p>Oder öffne die App: <a href="{app_link}">{app_link}</a></p>
    """
    _send(email, f"Neuer Quiz-Abend: {event_title}", body)

def send_rsvp_confirmation(participant_name: str, email: str, event_title: str, event_date: str):
    body = f"""
    <p>Hallo {participant_name},</p>
    <p>deine Zusage für <strong>{event_title}</strong> am <strong>{event_date}</strong> wurde aufgenommen.</p>
    <p>Wir melden uns, sobald der Termin gebucht wurde.</p>
    """
    _send(email, f"Zusage bestätigt: {event_title}", body)

def send_booking_confirmation(participant_name: str, email: str, event_title: str, event_date: str):
    body = f"""
    <p>Hallo {participant_name},</p>
    <p>der Termin <strong>{event_title}</strong> am <strong>{event_date}</strong> wurde erfolgreich gebucht. Wir sind dabei!</p>
    """
    _send(email, f"Termin gebucht: {event_title}", body)

def send_cancellation(participant_name: str, email: str, event_title: str, event_date: str):
    body = f"""
    <p>Hallo {participant_name},</p>
    <p>leider musste der Termin <strong>{event_title}</strong> am <strong>{event_date}</strong> storniert werden,
    da nicht genügend Teilnehmer zugesagt haben.</p>
    """
    _send(email, f"Termin storniert: {event_title}", body)

def send_reminder(participant_name: str, email: str, event_title: str, event_date: str):
    body = f"""
    <p>Hallo {participant_name},</p>
    <p>Erinnerung: <strong>{event_title}</strong> findet am <strong>{event_date}</strong> statt. Wir sehen uns!</p>
    """
    _send(email, f"Erinnerung: {event_title} steht an!", body)
