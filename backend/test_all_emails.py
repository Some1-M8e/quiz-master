"""
Test: Alle E-Mail-Typen generieren und an miriam.wassmann@adesso.de senden.
"""
import logging
from datetime import datetime, timedelta
from config import settings
from email_service import (
    send_invitation,
    send_rsvp_confirmation,
    send_booking_confirmation,
    send_booking_warning,
    send_cancellation,
    send_participant_welcome,
    send_participant_removed,
    send_reminder,
    send_maybe_reminder,
    send_weekly_reminder,
    send_maybe_timeout,
)

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

def main():
    print("=" * 80)
    print("ALLE E-MAIL-TYPEN - TEST")
    print("=" * 80)
    print()
    print(f"Alle E-Mails werden an: {settings.smtp_user} gesendet")
    print("(Trockenlauf im Log anzeigen)")
    print()

    # Test-Daten
    participant_name = "Miriam Wassmann"
    email = settings.smtp_user  # An die SMTP-User-Adresse senden
    event_title = "Verquiz Meinnicht - Sommer Quiz"
    event_date = (datetime.now() + timedelta(days=14)).strftime("%d.%m.%Y, 19:00 Uhr")
    event_description = "Ein spannender Quiz-Abend mit allgemeinen Wissensfragen"
    token = "test-token-12345"

    # 1. Registrierungs-Bestätigung (Participant Welcome)
    print("-" * 80)
    print("1. REGISTRIERUNGS-BESTÄTIGUNG (Participant Welcome)")
    print("-" * 80)
    send_participant_welcome(participant_name, email)
    print()

    # 2. Neue Event-Einladung (Invitation)
    print("-" * 80)
    print("2. NEUE EVENT-EINLADUNG (Invitation)")
    print("-" * 80)
    send_invitation(participant_name, email, event_title, event_date, token, event_description)
    print()

    # 3. RSVP-Bestätigung (Ja)
    print("-" * 80)
    print("3. RSVP-BESTÄTIGUNG - ZUSAGE (RSVP Confirmation - Yes)")
    print("-" * 80)
    send_rsvp_confirmation(participant_name, email, event_title, event_date, event_description, "yes")
    print()

    # 4. RSVP-Bestätigung (Vielleicht)
    print("-" * 80)
    print("4. RSVP-BESTÄTIGUNG - VIelleicht (RSVP Confirmation - Maybe)")
    print("-" * 80)
    send_rsvp_confirmation(participant_name, email, event_title, event_date, event_description, "maybe")
    print()

    # 5. Buchungs-Bestätigung (Ja)
    print("-" * 80)
    print("5. BUCHUNGS-BESTÄTIGUNG (Booking Confirmation)")
    print("-" * 80)
    send_booking_confirmation(participant_name, email, event_title, event_date, event_description, "yes")
    print()

    # 6. Buchungs-Bestätigung (Vielleicht)
    print("-" * 80)
    print("6. BUCHUNGS-BESTÄTIGUNG - MIT HINWEIS (Booking Confirmation - Maybe)")
    print("-" * 80)
    send_booking_confirmation(participant_name, email, event_title, event_date, event_description, "maybe")
    print()

    # 7. Warnung 7 Tage vorher (kritische Maybe-Stimmen)
    print("-" * 80)
    print("7. WARNUNG 7 TAGE VORHER (Booking Warning)")
    print("-" * 80)
    participants = [
        type('obj', (object,), {'email': email, 'name': 'Miriam'}),
    ]
    send_booking_warning(event_title, event_date, 3, 2, participants)
    print()

    # 8. Stornierung
    print("-" * 80)
    print("8. STORNIERUNG (Cancellation)")
    print("-" * 80)
    send_cancellation(participant_name, email, event_title, event_date, event_description)
    print()

    # 9. Erinnerung (Tag vor Event)
    print("-" * 80)
    print("9. ERINNERUNG - MORGEN IST ES SO WEIT (Reminder)")
    print("-" * 80)
    send_reminder(participant_name, email, event_title, event_date, event_description)
    print()

    # 10. Maybe-Erinnerung (48 Stunden Frist)
    print("-" * 80)
    print("10. MAYBE-ERINNERUNG (48h Frist) (Maybe Reminder)")
    print("-" * 80)
    send_maybe_reminder(participant_name, email, event_title, event_date, token, event_description)
    print()

    # 11. Wöchentliche Erinnerung
    print("-" * 80)
    print("11. WÖCHENTLICHE ERINNERUNG (Weekly Reminder)")
    print("-" * 80)
    send_weekly_reminder(participant_name, email, event_title, event_date, token, event_description)
    print()

    # 12. Entfernung aus der Liste
    print("-" * 80)
    print("12. ENTFERNUNG AUS DER LISTE (Participant Removed)")
    print("-" * 80)
    send_participant_removed(participant_name, email)
    print()

    # 13. Maybe-Timeout (48h Frist verstrichen)
    print("-" * 80)
    print("13. MAYBE-TIMEOUT - NICHT-ANTWORT ALS ABSCAGE GEWERTET (Maybe Timeout)")
    print("-" * 80)
    send_maybe_timeout(participant_name, email, event_title, event_date, event_description)
    print()

    print("=" * 80)
    print("ALLE E-MAIL-TYPEN ANGEZEIGT")
    print("=" * 80)

if __name__ == "__main__":
    main()
