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


def _send(to: str, subject: str, body_html: str, include_unsubscribe: bool = True):
    # Automatisierungs-Hinweis vor der Begrüßung hinzufügen
    automation_notice = (
        '<p style="background:#fef3c7;padding:8px 12px;border-radius:4px;margin:0 0 1rem 0;'
        'font-size:0.85rem;color:#92400e;border-left:3px solid #f59e0b;">'
        '<strong>Achtung:</strong> Diese E-Mail wurde automatisiert von einem Tool versendet. '
        'Bei Problemen wende dich bitte an Miriam Waßmann.</p>'
    )

    # Info-Block zum Tool Quizmaster hinzufügen
    tool_info = (
        '<div style="background:#f0f9ff;padding:12px;border-radius:8px;margin:0 0 1rem 0;'
        'font-size:0.85rem;color:#0c4a6e;border-left:3px solid #0284c7;">'
        '<strong>Über Quizmaster:</strong> Das Tool Quizmaster wurde dafür gebaut, neue Quiz-Termine '
        'bei der Pension Schmidt automatisch zu erkennen und direkt den spätmöglichsten Termin '
        'für den Quiz-Abend zu buchen (zwischen 19:00 und 19:30 Uhr). Erst nach der Buchung gehen '
        'die E-Mail-Anfragen an euch raus, ob ihr teilnehmen wollt.<br><br>'
        '<strong>Warum ist das so?</strong> Bisher hat die Pension Schmidt die Quiz-Termine nicht '
        'in regelmäßigen Abständen buchbar gemacht. Dadurch war ein ständiges Nachsehen erforderlich. '
        'Oft waren die Plätze dann schon weg. Daher werden jetzt immer 5 Plätze automatisch gebucht. '
        'Wenn nicht genügend Leute von uns zusammenkommen, dann storniert das Tool die Buchung von selbst. '
        'Weitere Hinweise findest du im Tool.</div>'
    )

    body_html = automation_notice + tool_info + body_html

    if settings.email_dry_run:
        logger.info(f"[DRY-RUN] E-Mail an {to} | Betreff: {subject}\n{body_html}")
        return
    if include_unsubscribe:
        # Unsubscribe-Link hinzufügen
        unsubscribe_link = f"{settings.app_url}/unsubscribe/{to}"
        body_html += f'<p style="margin-top:2rem;padding-top:1rem;border-top:1px solid #e5e7eb;font-size:0.8rem;color:#9ca3af;">' \
                     f'Du erhältst diese E-Mail weil du als Quiz-Interessierter eingetragen bist. ' \
                     f'<a href="{unsubscribe_link}">Benachrichtigungen abbestellen</a>.</p>'
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
    <p style=\"margin-top:1rem;padding-top:1rem;border-top:1px solid #e5e7eb;font-size:0.85rem;color:#6b7280;\">
        <strong>Hinweis:</strong> Dieser Termin wurde automatisch für 5 Personen gebucht.
        Die Buchung wird storniert, wenn nicht mindestens 4 feste Zusagen (Ja) vorliegen.
    </p>
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
        outro = "Der Termin wurde bereits für 5 Personen gebucht. Wir prüfen 7 Tage vor dem Event, ob genügend feste Zusagen vorliegen."
        subject = f"Zusage bestätigt: {event_title}"
    body = f"""
    <p>Hallo {participant_name},</p>
    <p>{intro}</p>
    {info}
    <p>{outro}</p>
    """
    _send(email, subject, body, include_unsubscribe=True)


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
    _send(email, f"Termin gebucht: {event_title}", body, include_unsubscribe=True)






def send_booking_warning(event_title: str, event_date: str, yes_count: int, maybe_count: int, participants: list):
    """
    Wird 7 Tage vor dem Event an alle Ja-Teilnehmer gesendet, wenn es kritische Maybe-Stimmen gibt.
    Informiert dass die Buchung storniert werden könnte wenn Maybe nicht zusagen.
    """
    MIN_PARTICIPANTS = 4
    info = _event_info_block(event_title, event_date, "")
    body = f"""
    <p>Hallo,</p>
    <p>7 Tage vor dem Quiz-Abend gibt es ein Update zur aktuellen Situation:</p>
    {info}
    <div style="background:#fef3c7;padding:12px;border-radius:8px;margin:1rem 0;border-left:4px solid #f59e0b;">
        <p style="margin:0;"><strong>Aktuelle Zusage:</strong></p>
        <p style="margin:4px 0 0 0;">
            <span style="color:#16a34a;font-weight:bold;">{yes_count} feste Zusagen (Ja)</span>
            {f' + {maybe_count} vielleicht' if maybe_count > 0 else ''}
        </p>
    </div>
    <p style="margin-top:1rem;"><strong style="color:#dc2626;">Achtung:</strong> Es gibt noch {maybe_count} Vielleicht-Antwort{ "n" if maybe_count > 1 else ""}. Wenn diese nicht innerhalb von 48 Stunden zu "Ja" werden, <strong>muss die Buchung möglicherweise storniert werden</strong>.</p>
    <p style="color:#6b7280;font-size:0.9rem;margin-top:0.5rem;">
        Vielleicht-Teilnehmer haben 48 Stunden Zeit sich definitiv zu entscheiden. Ohne Antwort werden sie automatisch als Absage gewertet.
    </p>
    <p style="margin-top:1rem;">Danke für dein Verständnis!</p>
    """
    for p in participants:
        if p.email:
            _send(p.email, f"Wichtiger Update zu {event_title}", body, include_unsubscribe=False)


def send_cancellation(participant_name: str, email: str, event_title: str, event_date: str, event_description: str = ""):
    info = _event_info_block(event_title, event_date, event_description)
    body = f"""
    <p>Hallo {participant_name},</p>
    <p>leider musste der folgende Termin storniert werden, da nicht genügend Teilnehmer zugesagt haben:</p>
    {info}
    """
    _send(email, f"Termin storniert: {event_title}", body, include_unsubscribe=True)


def send_participant_welcome(name: str, email: str):
    body = f"""
    <p>Hallo {name},</p>
    <p>du wurdest in die Liste der <strong>Quiz-Interessierten</strong> eingetragen und wirst ab sofort über neue Quiz-Abende benachrichtigt.</p>
    <p>Sobald ein neuer Termin gefunden wird, bekommst du eine E-Mail mit allen Details und kannst direkt zu- oder absagen.</p>
    """
    _send(email, "Du bist jetzt bei Quiz-Master dabei!", body, include_unsubscribe=True)


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
    """
    Wird 7 Tage vor dem Event an Maybe-Teilnehmer gesendet.
    48 Stunden Frist zur definitiven Entscheidung.
    """
    info = _event_info_block(event_title, event_date, event_description)
    yes_link = f"{settings.app_url}/rsvp/{token}/yes"
    no_link = f"{settings.app_url}/rsvp/{token}/no"
    body = f"""
    <p>Hallo {participant_name},</p>
    <p>7 Tage vor dem Quiz-Abend bitte um definitive Entscheidung — du hast <strong>48 Stunden Zeit</strong>!</p>
    {info}
    <p>
        <a href="{yes_link}" style="padding:8px 16px;background:#22c55e;color:white;text-decoration:none;border-radius:4px;">Zusagen</a>
        &nbsp;&nbsp;
        <a href="{no_link}" style="padding:8px 16px;background:#ef4444;color:white;text-decoration:none;border-radius:4px;">Absagen</a>
    </p>
    <p style="color:#6b7280;font-size:0.9rem;margin-top:0.5rem;">Wenn du nicht innerhalb von 48 Stunden antwortest, wird deine Anmeldung automatisch als Absage gewertet.</p>
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


def send_maybe_timeout(participant_name: str, email: str, event_title: str, event_date: str, event_description: str = ""):
    """
    Wird gesendet, wenn Maybe-Teilnehmer nach 48 Stunden Frist nicht reagiert haben.
    Informiert, dass ihre Nicht-Antwort als Absage gewertet wurde.
    """
    info = _event_info_block(event_title, event_date, event_description)
    body = f"""
    <p>Hallo {participant_name},</p>
    <p>leider hast du auf unsere Erinnerung zur definitiven Entscheidung nicht reagiert.</p>
    {info}
    <div style="background:#fee2e2;padding:12px;border-radius:8px;margin:1rem 0;border-left:4px solid #ef4444;">
        <p style="margin:0;"><strong style="color:#dc2626;">Dein Vielleicht wurde als Absage gewertet.</strong></p>
    </div>
    <p style="color:#6b7280;font-size:0.9rem;margin-top:0.5rem;">
        Bei zukünftigen Events wirst du wieder benachrichtigt, wenn du dich wieder anmelden möchtest.
    </p>
    <p style="margin-top:1rem;">Wir hoffen, dich bei einem anderen Event begrüßen zu dürfen!</p>
    """
    _send(email, f"Absage bestätigt: {event_title}", body, include_unsubscribe=False)


def send_event_found_notification(participant_name: str, email: str, event_title: str, event_date: str, event_description: str, detail_url: str):
    """
    Wird gesendet, wenn ein Event gefunden wurde das NICHT automatisch gebucht wird
    (z.B. "Wer wird Pensionär?"). Informiert über den gefundenen Termin mit Link zur Buchung.
    """
    info = _event_info_block(event_title, event_date, event_description)
    body = f"""
    <p>Hallo {participant_name},</p>
    <p>ein neuer Quiz-Termin wurde auf der Website der Pension Schmidt gefunden!</p>

    <div style="background:#fef3c7;padding:12px;border-radius:8px;margin:1rem 0;border-left:4px solid #f59e0b;">
        <p style="margin:0;"><strong style="color:#92400e;">Hinweis: Dieser Termin wird NICHT automatisch gebucht.</strong></p>
        <p style="margin:8px 0 0 0;color:#92400e;">Wenn du teilnehmen möchtest, bitte selbst buchen über den Link unten.</p>
    </div>

    {info}

    <p style="margin-top:1.5rem;">
        <a href="{detail_url}" style="display:inline-block;padding:10px 20px;background:#2563eb;color:white;text-decoration:none;border-radius:6px;font-weight:bold;">
            Zum Buchungstool
        </a>
    </p>

    <p style="color:#6b7280;font-size:0.9rem;margin-top:1rem;">
        Der Termin ist aktuell noch buchbar. Wir empfehlen, schnell zu sein – die Plätze sind begrenzt!
    </p>
    """
    _send(email, f"Neuer Quiz-Termin gefunden: {event_title}", body, include_unsubscribe=False)
