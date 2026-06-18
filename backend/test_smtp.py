"""
SMTP-Verbindungstest: Prüft ob die SMTP-Zugangsdaten korrekt sind.
"""
import smtplib
from config import settings

def test_smtp():
    print("=" * 60)
    print("SMTP-VERBINDUNGS-TEST")
    print("=" * 60)
    print()
    print(f"SMTP-Host: {settings.smtp_host}")
    print(f"SMTP-Port: {settings.smtp_port}")
    print(f"SMTP-Benutzer: {settings.smtp_user}")
    print(f"Passwort: {'*' * len(settings.smtp_password) if settings.smtp_password else '(leer)'}")
    print()
    print("-" * 60)

    try:
        # Verbindung aufbauen
        print(f"Verbinde mit {settings.smtp_host}:{settings.smtp_port}...")
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10)
        print("OK - Verbindung hergestellt")

        # STARTTLS aktivieren
        print("STARTTLS aktivieren...")
        server.starttls()
        print("OK - TLS aktiviert")

        # Anmelden
        print("Anmelden...")
        server.login(settings.smtp_user, settings.smtp_password)
        print("OK - Anmeldung erfolgreich!")

        server.quit()

        print()
        print("=" * 60)
        print("ERGEBNIS: SMTP-Konfiguration ist KORREKT!")
        print("=" * 60)
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"FEHLER: Authentifizierung fehlgeschlagen!")
        print(f"   - Prüfe Benutzername und Passwort")
        print(f"   - Eventuell wird ein App-Passwort benötigt")
        print(f"   - SMTP-Zugang muss im E-Mail-Konto aktiviert sein")
        print()
        print(f"Details: {e}")
        return False

    except smtplib.SMTPConnectError as e:
        print(f"FEHLER: Verbindung zum Server fehlgeschlagen!")
        print(f"   - Prüfe Internetverbindung")
        print(f"   - Prüfe ob Firewall den Zugriff blockiert")
        print(f"   - Prüfe ob SMTP-Host korrekt ist")
        print()
        print(f"Details: {e}")
        return False

    except Exception as e:
        print(f"FEHLER: Unerwarteter Fehler!")
        print(f"Details: {e}")
        return False

if __name__ == "__main__":
    test_smtp()
