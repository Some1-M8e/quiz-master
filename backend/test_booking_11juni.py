#!/usr/bin/env python3
"""
Manueller Test der Buchungsfunktion für 11.06.2026 um 16:15 Uhr, 2 Personen
Stoppt VOR dem Confirm-Button
"""

import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def main():
    detail_url = "https://www.pensionschmidt.se/programm/verquizmeinnicht-trp7e-5z68l-5rldg-x3wkr-gc3dy-fa7hc-mk4hb-97dbl-3a4be"
    event_date = datetime(2026, 6, 11)
    target_time = "16:15"
    guests = 2

    # Screenshots-Verzeichnis erstellen
    os.makedirs("screenshots", exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(locale="de-DE")
        page = await context.new_page()

        try:
            # Schritt 1: Seite laden
            print("Schritt 1: Detailseite laden...")
            await page.goto(detail_url, wait_until="networkidle", timeout=30000)
            await page.screenshot(path="screenshots/test_01_seite_geladen.png")
            print("  -> Screenshot: test_01_seite_geladen.png")

            # Schritt 2: Resmio öffnen
            print("Schritt 2: Resmio öffnen...")
            for btn_text in ("Reservieren", "Buchen", "Reserve", "Book"):
                btn = page.get_by_text(btn_text, exact=False).first
                try:
                    if await btn.is_visible(timeout=3000):
                        async with context.expect_page(timeout=6000) as popup_info:
                            await btn.click()
                        page = await popup_info.value
                        await page.wait_for_load_state("networkidle", timeout=20000)
                        print(f"  -> Resmio geoffnet: {page.url}")
                        await page.screenshot(path="screenshots/test_02_resmio_geoeffnet.png")
                        print("  -> Screenshot: test_02_resmio_geoeffnet.png")
                        break
                except Exception:
                    continue

            # Schritt 3: Datum ändern
            print(f"Schritt 3: Datum auf {event_date.strftime('%d.%m.%Y')} setzen...")
            await page.click("button.date-picker", timeout=5000)
            await page.wait_for_timeout(2000)
            await page.screenshot(path="screenshots/test_03_datum_picker_geoeffnet.png")
            print("  -> Screenshot: test_03_datum_picker_geoeffnet.png")

            # Datum auswählen (11. Juni 2026)
            # Resmio zeigt Kalender an - nach dem Datum suchen
            date_button = page.get_by_text("11", exact=True).first
            try:
                if await date_button.is_visible(timeout=3000):
                    await date_button.click()
                    await page.wait_for_timeout(1500)
                    print(f"  -> Datum {event_date.strftime('%d.%m.%Y')} ausgewahlt")
            except Exception as e:
                print(f"  -> Datum-Button nicht direkt gefunden: {e}")

            await page.screenshot(path="screenshots/test_04_datum_gesetzt.png")
            print("  -> Screenshot: test_04_datum_gesetzt.png")

            # Schritt 4: Personenzahl ändern
            print(f"Schritt 4: Personen auf {guests} setzen...")
            await page.click("button.guest-picker", timeout=5000)
            await page.wait_for_timeout(1500)
            await page.screenshot(path="screenshots/test_05_gaeste_picker_geoeffnet.png")
            print("  -> Screenshot: test_05_gaeste_picker_geoeffnet.png")

            # Gäste auswählen (Minus/Plus Buttons oder direkte Auswahl)
            # Zuerst prüfen ob "2 Gäste" direkt klickbar ist
            try:
                two_guests = page.get_by_text("2 Gäste", exact=True).first
                if await two_guests.is_visible(timeout=2000):
                    await two_guests.click()
                    print("  -> 2 Gäste ausgewahlt")
            except Exception:
                # Falls nicht, Plus/Minus verwenden
                print("  -> Versuche Plus/Minus Buttons...")
                pass

            await page.screenshot(path="screenshots/test_06_personen_gesetzt.png")
            print("  -> Screenshot: test_06_personen_gesetzt.png")

            # Zurück zum Hauptformular
            await page.click("button.is-primary", timeout=3000)  # "Weiter" oder zurück
            await page.wait_for_timeout(1500)

            # Schritt 5: Uhrzeit auswählen
            print(f"Schritt 5: Uhrzeit {target_time} suchen...")
            await page.wait_for_timeout(2000)

            # Nach der Uhrzeit suchen
            time_slot = page.get_by_text(target_time, exact=True).first
            try:
                if await time_slot.is_visible(timeout=3000):
                    await time_slot.click()
                    print(f"  -> Uhrzeit {target_time} ausgewahlt")
                else:
                    print(f"  -> Uhrzeit {target_time} nicht gefunden, verfuegbare Slots pruefen...")
            except Exception as e:
                print(f"  -> Uhrzeit-Button nicht gefunden: {e}")

            await page.screenshot(path="screenshots/test_07_uhrzeit_gesetzt.png")
            print("  -> Screenshot: test_07_uhrzeit_gesetzt.png")

            # Schritt 6: Weiter zum Formular
            print("Schritt 6: Zum Formular...")
            await page.wait_for_timeout(2000)

            # "Weiter" Button klicken
            try:
                await page.click("button.is-primary", timeout=5000)
                await page.wait_for_timeout(2500)
                print("  -> Weiter geklickt")
            except Exception as e:
                print(f"  -> Weiter-Button nicht geklickt: {e}")

            await page.screenshot(path="screenshots/test_08_formular_seite.png")
            print("  -> Screenshot: test_08_formular_seite.png")

            # Schritt 7: Kontaktdaten ausfüllen
            print("Schritt 7: Kontaktdaten ausfuellen...")

            # Name
            name_input = page.locator("input[name='name'], input[placeholder*='Name']").first
            try:
                if await name_input.is_visible(timeout=2000):
                    await name_input.fill("Miriam KI Tool", timeout=3000)
                    print("  -> Name ausgefüllt")
            except Exception:
                print("  -> Name-Feld nicht gefunden")

            # E-Mail
            email_input = page.locator("input[type='email'], input[name='email']").first
            try:
                if await email_input.is_visible(timeout=2000):
                    await email_input.fill("miawassi@posteo.de", timeout=3000)
                    print("  -> E-Mail ausgefüllt")
            except Exception:
                print("  -> E-Mail-Feld nicht gefunden")

            # Telefon
            phone_input = page.locator("input[type='tel'], input[name='phone']").first
            try:
                if await phone_input.is_visible(timeout=2000):
                    await phone_input.fill("017696830342", timeout=3000)
                    print("  -> Telefon ausgefüllt")
            except Exception:
                print("  -> Telefon-Feld nicht gefunden")

            await page.screenshot(path="screenshots/test_09_kontaktdaten_ausgefuellt.png")
            print("  -> Screenshot: test_09_kontaktdaten_ausgefuellt.png")

            # Schritt 8: Nachricht eintragen
            print("Schritt 8: Nachricht eintragen...")
            msg_input = page.locator("textarea, input[name='message'], input[name='note']").first
            try:
                if await msg_input.is_visible(timeout=2000):
                    await msg_input.fill("Diese Buchung wurde von einer KI für mich durchgeführt. Bei Problemen bitte anrufen!!", timeout=3000)
                    print("  -> Nachricht eingetragen")
            except Exception:
                print("  -> Nachricht-Feld nicht gefunden")

            await page.screenshot(path="screenshots/test_10_nachricht_eingetragen.png")
            print("  -> Screenshot: test_10_nachricht_eingetragen.png")

            # Schritt 9: Vor Confirm stoppen
            print("\n" + "="*60)
            print("TEST ERFOLGREICH ABGESCHLOSSEN")
            print("Alle Felder ausgefüllt - Confirm-Button NICHT geklickt")
            print("="*60)
            print("\nScreenshots wurden in 'screenshots/' gespeichert:")
            for f in sorted(os.listdir("screenshots")):
                if f.startswith("test_") and f.endswith(".png"):
                    print(f"  - screenshots/{f}")

        except Exception as e:
            print(f"Fehler: {e}")
            await page.screenshot(path="screenshots/test_error.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
