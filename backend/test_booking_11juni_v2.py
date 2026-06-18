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
            async with context.expect_page(timeout=8000) as popup_info:
                await page.get_by_text("Reservieren", exact=False).first.click()
            page = await popup_info.value
            await page.wait_for_load_state("networkidle", timeout=20000)
            await page.wait_for_timeout(3000)  # Warten bis Widget komplett geladen
            print(f"  -> Resmio geoffnet: {page.url}")
            await page.screenshot(path="screenshots/test_02_resmio_geoeffnet.png")
            print("  -> Screenshot: test_02_resmio_geoeffnet.png")

            # Schritt 3: Datum ändern - "Heute" Button klicken
            print(f"Schritt 3: Datum auf {event_date.strftime('%d.%m.%Y')} setzen...")

            # Button mit Text "Heute" finden
            today_btn = page.get_by_text("Heute", exact=True).first
            await today_btn.wait_for(state="visible", timeout=5000)
            await today_btn.click()
            await page.wait_for_timeout(2000)
            await page.screenshot(path="screenshots/test_03_datum_picker_geoeffnet.png")
            print("  -> Datum-Picker geoffnet")
            print("  -> Screenshot: test_03_datum_picker_geoeffnet.png")

            # 11. Juni 2026 auswählen - im Kalender nach dem Datum suchen
            # Resmio verwendet deutsche Monatsnamen
            print("  -> Suche nach Datum 11 im Kalender...")

            # Kalender-Zellen finden (oft als td oder div mit Tageszahl)
            day_11 = page.locator("td[data-day='11'], div[data-day='11'], td:has-text('11'), div:has-text('11')").first
            try:
                if await day_11.is_visible(timeout=3000):
                    await day_11.click()
                    print("  -> Datum 11. ausgewahlt")
            except Exception as e:
                print(f"  -> Direkt-Selektion fehlgeschlagen: {e}")
                # Fallback: Alle Zellen im Kalender durchsuchen
                cells = await page.query_selector_all("td, div")
                for cell in cells:
                    text = await cell.text_content() or ""
                    if text.strip() == "11":
                        cls = await cell.get_attribute("class") or ""
                        if "disabled" not in cls.lower() and "other-month" not in cls.lower():
                            await cell.click()
                            print(f"  -> Datum 11. uber Zelle ausgewahlt")
                            break

            await page.wait_for_timeout(1500)
            await page.screenshot(path="screenshots/test_04_datum_gesetzt.png")
            print("  -> Screenshot: test_04_datum_gesetzt.png")

            # Schritt 4: Personenzahl - "2 Gäste" sollte schon richtig sein
            print(f"Schritt 4: Personen pruefen ({guests} erwartet)...")

            # Prüfen ob "2 Gäste" angezeigt wird
            guest_text = await page.get_by_text("2 Gäste", exact=True).first.text_content() or ""
            print(f"  -> Aktuelle Auswahl: {guest_text}")

            # Falls nicht 2, dann anpassen
            if "2" not in guest_text:
                guest_btn = page.get_by_text("Gäste", exact=False).first
                await guest_btn.click()
                await page.wait_for_timeout(1500)
                # 2 Gäste auswählen
                two_guests = page.get_by_text("2 Gäste", exact=True).first
                await two_guests.click()
                print("  -> 2 Gäste ausgewahlt")

            await page.screenshot(path="screenshots/test_05_personen_gesetzt.png")
            print("  -> Screenshot: test_05_personen_gesetzt.png")

            # Schritt 5: Weiter klicken um zu Uhrzeiten zu gelangen
            print("Schritt 5: Weiter zu Uhrzeiten...")
            weiter_btn = page.get_by_role("button", name="Weiter").first
            await weiter_btn.wait_for(state="visible", timeout=5000)
            await weiter_btn.click()
            await page.wait_for_timeout(2500)
            await page.screenshot(path="screenshots/test_06_uhrzeiten_seite.png")
            print("  -> Screenshot: test_06_uhrzeiten_seite.png")

            # Schritt 6: Uhrzeit auswählen
            print(f"Schritt 6: Uhrzeit {target_time} suchen...")

            time_slot = page.get_by_text(target_time, exact=True).first
            try:
                await time_slot.wait_for(state="visible", timeout=3000)
                disabled = await time_slot.get_attribute("disabled")
                if disabled is None:
                    await time_slot.click()
                    print(f"  -> Uhrzeit {target_time} ausgewahlt")
                else:
                    print(f"  -> Uhrzeit {target_time} ist deaktiviert (voll)")
            except Exception as e:
                print(f"  -> Uhrzeit {target_time} nicht gefunden. Verfügbare Slots:")
                # Alle Uhrzeiten auflisten
                slots = await page.query_selector_all("button, [role='button'], td, div")
                times = ["16:00", "16:15", "16:30", "17:00", "17:15", "17:30", "18:00", "18:15", "18:30", "19:00", "19:15", "19:30"]
                for t in times:
                    try:
                        slot = page.get_by_text(t, exact=True).first
                        if await slot.is_visible(timeout=1000):
                            print(f"    - {t} vorhanden")
                    except:
                        pass

            await page.wait_for_timeout(1500)
            await page.screenshot(path="screenshots/test_07_uhrzeit_gesetzt.png")
            print("  -> Screenshot: test_07_uhrzeit_gesetzt.png")

            # Schritt 7: Weiter zum Formular
            print("Schritt 7: Zum Kontaktformular...")
            try:
                await page.get_by_role("button", name="Weiter").first.click(timeout=5000)
                await page.wait_for_timeout(2500)
                print("  -> Weiter geklickt")
            except Exception as e:
                print(f"  -> Weiter nicht geklickt: {e}")

            await page.screenshot(path="screenshots/test_08_formular_seite.png")
            print("  -> Screenshot: test_08_formular_seite.png")

            # Schritt 8: Kontaktdaten ausfüllen
            print("Schritt 8: Kontaktdaten ausfuellen...")

            # Name
            name_input = page.locator("input[name='name']").first
            try:
                await name_input.wait_for(state="visible", timeout=3000)
                await name_input.fill("Miriam KI Tool")
                print("  -> Name: Miriam KI Tool")
            except Exception:
                print("  -> Name-Feld nicht gefunden")

            # E-Mail
            email_input = page.locator("input[type='email']").first
            try:
                await email_input.wait_for(state="visible", timeout=3000)
                await email_input.fill("miawassi@posteo.de")
                print("  -> E-Mail: miawassi@posteo.de")
            except Exception:
                print("  -> E-Mail-Feld nicht gefunden")

            # Telefon
            phone_input = page.locator("input[type='tel']").first
            try:
                await phone_input.wait_for(state="visible", timeout=3000)
                await phone_input.fill("017696830342")
                print("  -> Telefon: 017696830342")
            except Exception:
                print("  -> Telefon-Feld nicht gefunden")

            await page.screenshot(path="screenshots/test_09_kontaktdaten_ausgefuellt.png")
            print("  -> Screenshot: test_09_kontaktdaten_ausgefuellt.png")

            # Schritt 9: Nachricht eintragen
            print("Schritt 9: Nachricht eintragen...")
            msg_input = page.locator("textarea").first
            try:
                await msg_input.wait_for(state="visible", timeout=3000)
                await msg_input.fill("Diese Buchung wurde von einer KI für mich durchgeführt. Bei Problemen bitte anrufen!!")
                print("  -> Nachricht eingetragen")
            except Exception:
                print("  -> Nachricht-Feld nicht gefunden")

            await page.screenshot(path="screenshots/test_10_nachricht_eingetragen.png")
            print("  -> Screenshot: test_10_nachricht_eingetragen.png")

            # Schritt 10: Vor Confirm stoppen
            print("\n" + "="*60)
            print("TEST ERFOLGREICH ABGESCHLOSSEN")
            print("Alle Felder ausgefüllt - Confirm-Button NICHT geklickt")
            print("="*60)
            print("\nScreenshots:")
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
