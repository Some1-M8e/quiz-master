"""
Test-E-Mail-Sendung: Versendet eine echte Registrierungs-Bestätigung.
"""
import logging
import importlib
from config import settings
from email_service import send_participant_welcome

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

def main():
    print("=" * 60)
    print("TEST: E-Mail-Sendung")
    print("=" * 60)
    print()
    print(f"SMTP_HOST: {settings.smtp_host}")
    print(f"SMTP_USER: {settings.smtp_user}")
    print(f"EMAIL_DRY_RUN: {settings.email_dry_run}")
    print()

    if settings.email_dry_run:
        print("WARNUNG: Dry-Run ist AKTIVIERT. Keine echte E-Mail wird gesendet.")
        print("Bitte EMAIL_DRY_RUN=false in der .env-Datei setzen und Python neu starten.")
    else:
        print("Dry-Run ist DEAKTIVIERT. Echte E-Mail wird gesendet...")
    print()

    # Test-E-Mail an miriam.wassmann@adesso.de senden
    send_participant_welcome(
        name="Miriam Wassmann",
        email="miriam.wassmann@adesso.de"
    )

    print()
    print("=" * 60)
    print("Test abgeschlossen!")
    print("=" * 60)

if __name__ == "__main__":
    main()
