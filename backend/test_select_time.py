#!/usr/bin/env python3
"""
Test: Uhrzeit explizit anklicken und pruefen ob Weiter aktiv wird
"""

import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    detail_url = "https://www.pensionschmidt.se/programm/verquizmeinnicht-trp7e-5z68l-5rldg-x3wkr-gc3dy-fa7hc-mk4hb-97dbl-3a4be"

    os.makedirs("screenshots", exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(locale="de-DE")
        page = await context.new_page()

        try:
            await page.goto(detail_url, wait_until="networkidle", timeout=30000)

            # Resmio öffnen
            async with context.expect_page(timeout=8000) as popup_info:
                await page.get_by_text("Reservieren", exact=False).first.click()
            page = await popup_info.value
            await page.wait_for_load_state("networkidle", timeout=20000)
            await page.wait_for_timeout(2000)

            # Datum-Picker öffnen
            await page.get_by_text("Heute", exact=True).first.click()
            await page.wait_for_timeout(2000)

            # Tag 11 auswählen
            await page.get_by_text("11", exact=True).first.click()
            await page.wait_for_timeout(2000)

            print("Uhrzeit 16:00 auswählen...")
            # Uhrzeit 16:00 klicken
            time_1600 = page.get_by_text("16:00", exact=True).first
            await time_1600.wait_for(state="visible", timeout=3000)

            # Prüfen ob disabled
            disabled = await time_1600.get_attribute("disabled")
            cls = await time_1600.get_attribute("class") or ""
            print(f"  16:00: disabled={disabled is not None}, class='{cls}'")

            await time_1600.click(force=True)
            await page.wait_for_timeout(2000)

            await page.screenshot(path="screenshots/after_time_click.png")

            # Prüfen ob Weiter jetzt aktiv ist
            weiter = page.get_by_role("button", name="Weiter").first
            is_enabled = await weiter.is_enabled()
            print(f"Weiter-Button aktiv nach 16:00 Klick: {is_enabled}")

            # Alle Buttons nochmal prüfen
            print("\nButtons nach Uhrzeit-Auswahl:")
            buttons = await page.query_selector_all("button, [role='button']")
            for i, btn in enumerate(buttons):
                text = await btn.text_content() or ""
                disabled = await btn.get_attribute("disabled")
                if text.strip():
                    print(f"  {i+1}. '{text.strip()}' disabled={disabled is not None}")

            # Versuch: Weiter klicken
            if is_enabled:
                print("\nWeiter klicken...")
                await weiter.click()
                await page.wait_for_timeout(3000)
                await page.screenshot(path="screenshots/after_weiter_click.png")
                print("Weiter geklickt!")
            else:
                print("\nWeiter immer noch deaktiviert - versuche andere Uhrzeiten...")
                for t in ["16:15", "16:30", "17:00"]:
                    try:
                        slot = page.get_by_text(t, exact=True).first
                        if await slot.is_visible(timeout=1000):
                            cls = await slot.get_attribute("class") or ""
                            disabled = await slot.get_attribute("disabled")
                            print(f"  {t}: disabled={disabled is not None}, class='{cls}'")
                            if disabled is None:
                                await slot.click(force=True)
                                await page.wait_for_timeout(1000)
                                if await weiter.is_enabled():
                                    print(f"  -> Weiter jetzt aktiv mit {t}!")
                                    break
                    except Exception as e:
                        print(f"  {t}: Fehler - {e}")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
