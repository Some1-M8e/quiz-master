#!/usr/bin/env python3
"""
Test-Buchung: 11.06.2026, 16:15 Uhr, 2 Personen
Stoppt VOR dem Confirm-Button
"""

import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def main():
    detail_url = "https://www.pensionschmidt.se/programm/verquizmeinnicht-trp7e-5z68l-5rldg-x3wkr-gc3dy-fa7hc-mk4hb-97dbl-3a4be"
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
            print("  -> OK")

            # Schritt 2: Resmio öffnen
            print("Schritt 2: Resmio öffnen...")
            async with context.expect_page(timeout=8000) as popup_info:
                await page.get_by_text("Reservieren", exact=False).first.click()
            page = await popup_info.value
            await page.wait_for_load_state("networkidle", timeout=20000)
            await page.wait_for_timeout(3000)
            await page.screenshot(path="screenshots/test_02_resmio_geoeffnet.png")
            print("  -> OK")

            # Schritt 3: Datum öffnen
            print("Schritt 3: Datum-Picker öffnen...")
            await page.get_by_text("Heute", exact=True).first.click()
            await page.wait_for_timeout(2000)
            await page.screenshot(path="screenshots/test_03_datum_picker_geoeffnet.png")

            # Prüfen welcher Monat angezeigt wird
            calendar_header = page.locator(".calendar-header, .month-header, [class*='calendar']").first
            header_text = await calendar_header.text_content() or "Nicht gefunden"
            print(f"  -> Kalender-Header: {header_text}")

            # Versuchen, alle Tageszahlen im Kalender zu finden
            print("  -> Verfügbare Tage im Kalender:")
            cells = await page.query_selector_all("td")
            days = []
            for cell in cells:
                text = await cell.text_content() or ""
                cls = await cell.get_attribute("class") or ""
                if text.strip() and text.strip().isdigit() and "other-month" not in cls.lower():
                    days.append(text.strip())
            print(f"     Tage: {', '.join(days[:10])}..." if len(days) > 10 else f"     Tage: {', '.join(days)}")

            # Prüfen ob 11 verfügbar ist
            day_11 = None
            for cell in cells:
                text = await cell.text_content() or ""
                cls = await cell.get_attribute("class") or ""
                if text.strip() == "11" and "other-month" not in cls.lower() and "disabled" not in cls.lower():
                    day_11 = cell
                    break

            if day_11:
                print("  -> Tag 11 gefunden und ausgewählt")
                await day_11.click()
                await page.wait_for_timeout(1500)
            else:
                print("  -> Tag 11 nicht im aktuellen Monat gefunden!")
                print("     Versuche zum richtigen Monat zu navigieren...")
                # Nächster Monat Button suchen
                next_month = page.get_by_label("Nächster Monat").first
                try:
                    if await next_month.is_visible(timeout=2000):
                        print("     Nächster Monat Button gefunden")
                        # Mehrmals klicken bis Juni 2026 erreicht ist
                        for i in range(12):  # Max 12 Monate vorwärts
                            await next_month.click()
                            await page.wait_for_timeout(500)
                            # Prüfen ob 11 verfügbar ist
                            for cell in await page.query_selector_all("td"):
                                text = await cell.text_content() or ""
                                if text.strip() == "11":
                                    await cell.click()
                                    print(f"     Tag 11 nach {i+1} Klicks gefunden")
                                    break
                except Exception as e:
                    print(f"     Fehler bei Monats-Navigation: {e}")

            await page.screenshot(path="screenshots/test_04_datum_gesetzt.png")

            # Schritt 4: Personen prüfen
            print("Schritt 4: Personen pruefen...")
            guest_text = await page.get_by_text("2 Gäste", exact=True).first.text_content() or ""
            print(f"  -> Aktuelle Auswahl: {guest_text}")
            await page.screenshot(path="screenshots/test_05_personen_gesetzt.png")

            # Schritt 5: Weiter zu Uhrzeiten
            print("Schritt 5: Weiter zu Uhrzeiten...")
            # Zuerst den Datum-Picker schließen (evtl. außerhalb klicken oder "Zurück")
            await page.wait_for_timeout(2000)

            # Prüfen ob "Weiter" jetzt aktiv ist
            weiter_btn = page.get_by_role("button", name="Weiter").first
            is_enabled = await weiter_btn.is_enabled()
            print(f"  -> Weiter-Button aktiv: {is_enabled}")

            if is_enabled:
                await weiter_btn.click()
                await page.wait_for_timeout(2500)
            else:
                print("  -> Weiter noch deaktiviert, warte...")
                await page.wait_for_timeout(5000)
                if await weiter_btn.is_enabled():
                    await weiter_btn.click()
                    await page.wait_for_timeout(2500)

            await page.screenshot(path="screenshots/test_06_uhrzeiten_seite.png")

            # Schritt 6: Uhrzeiten auflisten
            print("Schritt 6: Verfügbare Uhrzeiten pruefen...")
            times = ["16:00", "16:15", "16:30", "17:00", "17:15", "17:30", "18:00", "18:15", "18:30", "19:00", "19:15", "19:30"]
            available = []
            for t in times:
                try:
                    slot = page.get_by_text(t, exact=True).first
                    if await slot.is_visible(timeout=1000):
                        disabled = await slot.get_attribute("disabled")
                        if disabled is None:
                            available.append(t)
                            print(f"  -> {t}: VERFÜGBAR")
                        else:
                            print(f"  -> {t}: deaktiviert")
                except:
                    pass

            if available:
                print(f"Verfügbare Slots: {available}")
                # Gewünschte Uhrzeit oder erste verfügbare auswählen
                chosen = target_time if target_time in available else available[0]
                print(f"Wähle: {chosen}")
                await page.get_by_text(chosen, exact=True).first.click()
                await page.wait_for_timeout(1500)
            else:
                print("KEINE Uhrzeiten verfügbar!")

            await page.screenshot(path="screenshots/test_07_uhrzeit_gesetzt.png")

            # Schritt 7: Zum Formular
            print("Schritt 7: Zum Kontaktformular...")
            if await page.get_by_role("button", name="Weiter").first.is_enabled():
                await page.get_by_role("button", name="Weiter").first.click()
                await page.wait_for_timeout(2500)
            await page.screenshot(path="screenshots/test_08_formular_seite.png")

            # Schritt 8: Kontaktdaten
            print("Schritt 8: Kontaktdaten ausfuellen...")
            try:
                await page.locator("input[name='name']").first.fill("Miriam KI Tool")
                print("  -> Name: Miriam KI Tool")
            except: pass
            try:
                await page.locator("input[type='email']").first.fill("miawassi@posteo.de")
                print("  -> E-Mail: miawassi@posteo.de")
            except: pass
            try:
                await page.locator("input[type='tel']").first.fill("017696830342")
                print("  -> Telefon: 017696830342")
            except: pass
            await page.screenshot(path="screenshots/test_09_kontaktdaten_ausgefuellt.png")

            # Schritt 9: Nachricht
            print("Schritt 9: Nachricht eintragen...")
            try:
                await page.locator("textarea").first.fill("Diese Buchung wurde von einer KI für mich durchgeführt. Bei Problemen bitte anrufen!!")
                print("  -> Nachricht eingetragen")
            except:
                print("  -> Nachricht-Feld nicht gefunden")
            await page.screenshot(path="screenshots/test_10_nachricht_eingetragen.png")

            # Fertig
            print("\n" + "="*60)
            print("TEST ABGESCHLOSSEN - Vor Confirm gestoppt")
            print("="*60)
            print("\nScreenshots in 'screenshots/':")
            for f in sorted(os.listdir("screenshots")):
                if f.startswith("test_") and f.endswith(".png"):
                    print(f"  - {f}")

        except Exception as e:
            print(f"Fehler: {e}")
            await page.screenshot(path="screenshots/test_error.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
