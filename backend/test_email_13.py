"""
Test: Maybe-Timeout E-Mail (Nummer 13) senden.
"""
import logging
from datetime import datetime, timedelta
from config import settings
from email_service import send_maybe_timeout

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

def main():
    print("=" * 80)
    print("TEST: Maybe-Timeout E-Mail (Nummer 13)")
    print("=" * 80)
    print()

    # Test-Daten
    participant_name = "Miriam Wassmann"
    email = settings.smtp_user
    event_title = "Verquiz Meinnicht - Sommer Quiz"
    event_date = (datetime.now() + timedelta(days=14)).strftime("%d.%m.%Y, 19:00 Uhr")
    event_description = "Ein spannender Quiz-Abend mit allgemeinen Wissensfragen"

    # E-Mail senden
    send_maybe_timeout(participant_name, email, event_title, event_date, event_description)

    print()
    print("=" * 80)
    print("E-Mail wurde gesendet!")
    print("=" * 80)

if __name__ == "__main__":
    main()
