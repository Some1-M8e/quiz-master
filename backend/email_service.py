import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings

logger = logging.getLogger(__name__)


def _quiz_category(title: str) -> str | None:
    t = title.lower()
    if "verquizmeinnicht" in t or "verquiz meinnicht" in t:
        return "Allgemeinwissensquiz"
    if "quiz quiz bang bang" in t:
        return "Filme- und Serien-Quiz"
    return None


def _event_info_block(event_title: str, event_date: str, event_description: str) -> str:
    category = _quiz_category(event_title)
    category_html = ""
    if category:
        category_html = (
            f'<p style="margin:0 0 8px 0;">'
            f'<span style="background:#6366f1;color:white;padding:3px 10px;border-radius:12px;font-size:0.85rem;">'
            f'{category}</span></p>'
        )
    desc_html = ""
    if event_description:
        desc_html = f'<p style="margin:8px 0 0 0;color:#374151;">{event_description}</p>'

    return f"""
    <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin:16px 0;">
        {category_html}
        <p style="margin:0;font-size:1.05rem;"><strong>{event_title}</strong></p>
        <p style="margin:4px 0 0 0;color:#6b7280;">{event_date}</p>
        {desc_html}
    </div>
    """


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


def send_invitation(participant_name: str, email: str, event_title: str, event_date: str, token: str, event_description: str = ""):
    rsvp_yes = f"{settings.app_url}/rsvp/{token}/yes"
    rsvp_maybe = f"{settings.app_url}/rsvp/{token}/maybe"
    rsvp_no = f"{settings.app_url}/rsvp/{token}/no"
    app_link = f"{settings.app_url}/rsvp/{token}"
    info = _event_info_block(event_title, event_date, event_description)
    body = f"""
    <p>Hallo {participant_name},</p>
    <p>es gibt einen neuen Quiz-Abend-Termin:</p>
    {info}
    <p>Bist du dabei?</p>
    <p>
        <a href="{rsvp_yes}" style="padding:8px 16px;background:#22c55e;color:white;text-decoration:none;border-radius:4px;">Zusagen</a>
        &nbsp;&nbsp;
        <a href="{rsvp_maybe}" style="padding:8px 16px;background:#f59e0b;color:white;text-decoration:none;border-radius:4px;">Vielleicht</a>
        &nbsp;&nbsp;
        <a href="{rsvp_no}" style="padding:8px 16px;background:#ef4444;color:white;text-decoration:none;border-radius:4px;">Absagen</a>
    </p>
    <p>Oder öffne die App: <a href="{app_link}">{app_link}</a></p>
    """
    _send(email, f"Neuer Quiz-Abend: {event_title}", body)


def send_rsvp_confirmation(participant_name: str, email: str, event_title: str, event_date: str, event_description: str = "", response: str = "yes"):
    info = _event_info_block(event_title, event_date, event_description)
    if response == "maybe":
        intro = "dein 'Vielleicht' wurde aufgenommen:"
        outro = "Sag uns gerne noch Bescheid, sobald du weißt ob du dabei bist."
        subject = f"Vielleicht dabei: {event_title}"
    else:
        intro = "deine Zusage wurde aufgenommen:"
        outro = "Wir melden uns, sobald der Termin gebucht wurde."
        subject = f"Zusage bestätigt: {event_title}"
    body = f"""
    <p>Hallo {participant_name},</p>
    <p>{intro}</p>
    {info}
    <p>{outro}</p>
    """
    _send(email, subject, body)


def send_booking_confirmation(participant_name: str, email: str, event_title: str, event_date: str, event_description: str = "", response: str = "yes"):
    info = _event_info_block(event_title, event_date, event_description)
    if response == "maybe":
        intro = "der folgende Termin wurde erfolgreich gebucht — wir sind dabei!"
        hint = "<p style=\"color:#f59e0b;margin-top:1rem;\"><strong>Wichtig:</strong> Du hattest 'Vielleicht' geantwortet. Deine endgültige Teilnahme wird 1 Woche vor dem Event nochmal überprüft.</p>"
    else:
        intro = "der folgende Termin wurde erfolgreich gebucht — wir sind dabei!"
        hint = ""
    body = f"""
    <p>Hallo {participant_name},</p>
    <p>{intro}</p>
    {info}
    {hint}
    """
    _send(email, f"Termin gebucht: {event_title}", body)


def send_cancellation(participant_name: str, email: str, event_title: str, event_date: str, event_description: str = ""):
    info = _event_info_block(event_title, event_date, event_description)
    body = f"""
    <p>Hallo {participant_name},</p>
    <p>leider musste der folgende Termin storniert werden, da nicht genügend Teilnehmer zugesagt haben:</p>
    {info}
    """
    _send(email, f"Termin storniert: {event_title}", body)


def send_participant_welcome(name: str, email: str):
    body = f"""
    <p>Hallo {name},</p>
    <p>du wurdest in die Liste der <strong>Quiz-Interessierten</strong> eingetragen und wirst ab sofort über neue Quiz-Abende benachrichtigt.</p>
    <p>Sobald ein neuer Termin gefunden wird, bekommst du eine E-Mail mit allen Details und kannst direkt zu- oder absagen.</p>
    """
    _send(email, "Du bist jetzt bei Quiz-Master dabei!", body)


def send_participant_removed(name: str, email: str):
    body = f"""
    <p>Hallo {name},</p>
    <p>du wurdest aus der Liste der Quiz-Interessierten entfernt und erhältst keine weiteren Benachrichtigungen mehr.</p>
    """
    _send(email, "Du wurdest aus Quiz-Master entfernt", body)


def send_reminder(participant_name: str, email: str, event_title: str, event_date: str, event_description: str = ""):
    info = _event_info_block(event_title, event_date, event_description)
    body = f"""
    <p>Hallo {participant_name},</p>
    <p>Erinnerung: Morgen ist es so weit!</p>
    {info}
    <p>Wir sehen uns!</p>
    """
    _send(email, f"Erinnerung: {event_title} steht an!", body)


def send_maybe_reminder(participant_name: str, email: str, event_title: str, event_date: str, token: str, event_description: str = ""):
    info = _event_info_block(event_title, event_date, event_description)
    yes_link = f"{settings.app_url}/rsvp/{token}/yes"
    no_link = f"{settings.app_url}/rsvp/{token}/no"
    body = f"""
    <p>Hallo {participant_name},</p>
    <p>es ist noch eine Woche bis zum Quiz-Abend. Bitte bestätige deine Teilnahme oder sage ab — du hast 24 Stunden Zeit!</p>
    {info}
    <p>
        <a href="{yes_link}" style="padding:8px 16px;background:#22c55e;color:white;text-decoration:none;border-radius:4px;">Zusagen</a>
        &nbsp;&nbsp;
        <a href="{no_link}" style="padding:8px 16px;background:#ef4444;color:white;text-decoration:none;border-radius:4px;">Absagen</a>
    </p>
    <p>Wenn du nicht antwortest, wird deine Anmeldung als Absage gewertet.</p>
    """
    _send(email, f"Bestätigung nötig: {event_title}", body)


def send_weekly_reminder(participant_name: str, email: str, event_title: str, event_date: str, token: str, event_description: str = ""):
    info = _event_info_block(event_title, event_date, event_description)
    yes_link = f"{settings.app_url}/rsvp/{token}/yes"
    no_link = f"{settings.app_url}/rsvp/{token}/no"
    maybe_link = f"{settings.app_url}/rsvp/{token}/maybe"
    body = f"""
    <p>Hallo {participant_name},</p>
    <p>eine wöchentliche Erinnerung zum Quiz-Abend:</p>
    {info}
    <p>
        <a href="{yes_link}" style="padding:8px 16px;background:#22c55e;color:white;text-decoration:none;border-radius:4px;">Zusagen</a>
        &nbsp;&nbsp;
        <a href="{maybe_link}" style="padding:8px 16px;background:#f59e0b;color:white;text-decoration:none;border-radius:4px;">Vielleicht</a>
        &nbsp;&nbsp;
        <a href="{no_link}" style="padding:8px 16px;background:#ef4444;color:white;text-decoration:none;border-radius:4px;">Absagen</a>
    </p>
    <p>Falls du noch nicht geantwortet hast, bitte teil uns mit, ob du dabei bist. Danke!</p>
    """
    _send(email, f"Erinnerung: {event_title}", body)
