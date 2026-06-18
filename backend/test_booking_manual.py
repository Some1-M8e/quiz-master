#!/usr/bin/env python3
"""
Manueller Test der Buchungsfunktion:
- Datum: 11.06.2026
- Uhrzeit: 16:15 Uhr (wenn verfuegbar)
- Personen: 2
- Stoppt VOR dem Confirm-Button
"""

import asyncio
from datetime import datetime
from booking import book_event

async def main():
    # Test-Daten
    detail_url = "https://www.pensionschmidt.se/programm/verquizmeinnicht-trp7e-5z68l-5rldg-x3wkr-gc3dy-fa7hc-mk4hb-97dbl-3a4be"
    event_date = datetime(2026, 6, 11, 16, 15)  # 11.06.2026 um 16:15 Uhr
    event_title = "VerQUIZmeinnicht am 11.06.2026"

    print("=" * 60)
    print("TEST-BUCHUNG STARTEN")
    print("=" * 60)
    print(f"URL: {detail_url}")
    print(f"Datum: {event_date.strftime('%d.%m.%Y')}")
    print(f"Uhrzeit: 16:15 (wenn verfügbar)")
    print(f"Personen: 2")
    print(f"Stopp vor Confirm: JA")
    print("=" * 60)

    # Buchung starten (stop_before_confirm=True)
    success = await book_event(
        detail_url=detail_url,
        event_date=event_date,
        event_title=event_title,
        stop_before_confirm=True,
        custom_guests=2
    )

    print("=" * 60)
    if success:
        print("TEST ERFOLGREICH ABGESCHLOSSEN")
        print("Screenshots wurden in 'screenshots/' gespeichert")
    else:
        print("TEST FEHLGESCHLAGEN - Fehler im Log prüfen")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
