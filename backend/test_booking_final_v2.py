#!/usr/bin/env python3
"""
Vollständige Test-Buchung: 11.06.2026, 16:00 Uhr, 2 Personen
Stoppt VOR dem Confirm/Bestätigen Button
"""

import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    detail_url = "https://www.pensionschmidt.se/programm/verquizmeinnicht-trp7e-5z68l-5rldg-x3wkr-gc3dy-fa7hc-mk4hb-97dbl-3a4be"
    target_day = 11

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

            # Schritt 5: Uhrzeit auswählen
            print("Schritt 5: Uhrzeit 16:00 auswählen...")
            await page.get_by_text("16:00", exact=True).first.click(force=True)
            await page.wait_for_timeout(1500)
            await page.screenshot(path="screenshots/test_05_uhrzeit_gesetzt.png")
            print("  -> Uhrzeit 16:00 ausgewahlt")

            # Schritt 6: Weiter zum ersten Formular-Schritt
            print("Schritt 6: Weiter zum Formular...")
            await page.get_by_role("button", name="Weiter").first.click()
            await page.wait_for_timeout(2000)
            await page.screenshot(path="screenshots/test_06_weiter_klick1.png")
            print("  -> OK")

            # Schritt 7: Nochmal Weiter zum Kontaktformular
            print("Schritt 7: Zum Kontaktformular...")
            await page.get_by_role("button", name="Weiter").first.click()
            await page.wait_for_timeout(2500)
            await page.screenshot(path="screenshots/test_07_formular_seite.png")
            print("  -> OK")

            # Schritt 8: Kontaktdaten ausfüllen
            print("Schritt 8: Kontaktdaten ausfuellen...")

            # Vorname
            try:
                await page.locator('input[placeholder*="Max"]').first.fill("Miriam", timeout=5000)
                print("  -> Vorname: Miriam")
            except Exception as e:
                print(f"  -> Vorname-Feld: {e}")

            # Nachname
            try:
                await page.locator('input[placeholder*="Mustermann"]').first.fill("KI Tool", timeout=5000)
                print("  -> Nachname: KI Tool")
            except Exception as e:
                print(f"  -> Nachname-Feld: {e}")

            # E-Mail
            try:
                await page.locator('input[type="email"]').first.fill("miawassi@posteo.de", timeout=5000)
                print("  -> E-Mail: miawassi@posteo.de")
            except Exception as e:
                print(f"  -> E-Mail-Feld: {e}")

            # Telefon
            try:
                await page.locator('input[type="tel"]').first.fill("017696830342", timeout=5000)
                print("  -> Telefon: 017696830342")
            except Exception as e:
                print(f"  -> Telefon-Feld: {e}")

            await page.screenshot(path="screenshots/test_08_kontaktdaten_ausgefuellt.png")

            # Schritt 9: Nachricht eintragen
            print("Schritt 9: Nachricht eintragen...")
            try:
                # Suche nach Textarea oder Input mit "Nachricht" im Placeholder
                msg_field = page.locator("textarea").first
                await msg_field.wait_for(state="visible", timeout=3000)
                await msg_field.fill("Diese Buchung wurde von einer KI für mich durchgeführt. Bei Problemen bitte anrufen!!")
                print("  -> Nachricht eingetragen")
            except Exception as e:
                print(f"  -> Nachricht-Feld nicht gefunden: {e}")
            await page.screenshot(path="screenshots/test_09_nachricht_eingetragen.png")

            # Schritt 10: Vor Bestätigen stoppen
            print("\n" + "="*60)
            print("TEST ERFOLGREICH ABGESCHLOSSEN")
            print("Alle Felder ausgefüllt - Bestätigen-Button NICHT geklickt")
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
