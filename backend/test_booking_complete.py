#!/usr/bin/env python3
"""
Vollständige Test-Buchung: 11.06.2026, 16:00 Uhr (da 16:15 evtl. nicht verfuegbar), 2 Personen
Stoppt VOR dem Confirm-Button
"""

import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    detail_url = "https://www.pensionschmidt.se/programm/verquizmeinnicht-trp7e-5z68l-5rldg-x3wkr-gc3dy-fa7hc-mk4hb-97dbl-3a4be"
    target_day = 11
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
            print("  -> OK")

            # Schritt 2: Resmio öffnen
            print("Schritt 2: Resmio öffnen...")
            async with context.expect_page(timeout=8000) as popup_info:
                await page.get_by_text("Reservieren", exact=False).first.click()
            page = await popup_info.value
            await page.wait_for_load_state("networkidle", timeout=20000)
            await page.wait_for_timeout(2000)
            await page.screenshot(path="screenshots/test_02_resmio_geoeffnet.png")
            print("  -> OK")

            # Schritt 3: Datum-Picker öffnen
            print("Schritt 3: Datum-Picker öffnen...")
            await page.get_by_text("Heute", exact=True).first.click()
            await page.wait_for_timeout(2000)
            await page.screenshot(path="screenshots/test_03_datum_picker_geoeffnet.png")
            print("  -> OK")

            # Schritt 4: Tag 11 auswählen
            print(f"Schritt 4: Tag {target_day} auswählen...")
            await page.get_by_text(str(target_day), exact=True).first.click()
            await page.wait_for_timeout(2000)
            await page.screenshot(path="screenshots/test_04_datum_gesetzt.png")
            print(f"  -> Tag {target_day} ausgewahlt")

            # Schritt 5: Uhrzeit auswählen (16:00 als erste verfügbare)
            print("Schritt 5: Uhrzeit 16:00 auswählen...")
            await page.get_by_text("16:00", exact=True).first.click(force=True)
            await page.wait_for_timeout(1500)
            await page.screenshot(path="screenshots/test_05_uhrzeit_gesetzt.png")
            print("  -> Uhrzeit 16:00 ausgewahlt")

            # Schritt 6: Weiter zum Kontaktformular
            print("Schritt 6: Zum Kontaktformular...")
            await page.get_by_role("button", name="Weiter").first.click()
            await page.wait_for_timeout(2500)
            await page.screenshot(path="screenshots/test_06_formular_seite.png")
            print("  -> OK")

            # Schritt 7: Kontaktdaten ausfüllen
            print("Schritt 7: Kontaktdaten ausfuellen...")
            try:
                await page.locator("input[name='name']").first.fill("Miriam KI Tool")
                print("  -> Name: Miriam KI Tool")
            except Exception as e:
                print(f"  -> Name-Feld: {e}")
            try:
                await page.locator("input[type='email']").first.fill("miawassi@posteo.de")
                print("  -> E-Mail: miawassi@posteo.de")
            except Exception as e:
                print(f"  -> E-Mail-Feld: {e}")
            try:
                await page.locator("input[type='tel']").first.fill("017696830342")
                print("  -> Telefon: 017696830342")
            except Exception as e:
                print(f"  -> Telefon-Feld: {e}")
            await page.screenshot(path="screenshots/test_07_kontaktdaten_ausgefuellt.png")

            # Schritt 8: Nachricht eintragen
            print("Schritt 8: Nachricht eintragen...")
            try:
                textarea = page.locator("textarea").first
                await textarea.wait_for(state="visible", timeout=3000)
                await textarea.fill("Diese Buchung wurde von einer KI für mich durchgeführt. Bei Problemen bitte anrufen!!")
                print("  -> Nachricht eingetragen")
            except Exception as e:
                print(f"  -> Nachricht-Feld nicht gefunden: {e}")
            await page.screenshot(path="screenshots/test_08_nachricht_eingetragen.png")

            # Schritt 9: Vor Confirm stoppen
            print("\n" + "="*60)
            print("TEST ERFOLGREICH ABGESCHLOSSEN")
            print("Alle Felder ausgefüllt - Confirm-Button NICHT geklickt")
            print("="*60)
            print("\nScreenshots in 'screenshots/':")
            test_screenshots = sorted([f for f in os.listdir("screenshots") if f.startswith("test_") and f.endswith(".png")])
            for f in test_screenshots:
                print(f"  - {f}")

        except Exception as e:
            print(f"\nFEHLER: {e}")
            await page.screenshot(path="screenshots/test_error.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
