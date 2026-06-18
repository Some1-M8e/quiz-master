#!/usr/bin/env python3
"""
Debug: Pruefe ob Uhrzeiten nach Datum-Auswahl angezeigt werden
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
            await page.wait_for_timeout(3000)

            # Screenshot nach Datum-Auswahl
            await page.screenshot(path="screenshots/check_after_date.png")

            # Prüfen was auf der Seite ist
            print("Buttons nach Datum-Auswahl:")
            buttons = await page.query_selector_all("button, [role='button']")
            for i, btn in enumerate(buttons):
                text = await btn.text_content() or ""
                cls = await btn.get_attribute("class") or ""
                disabled = await btn.get_attribute("disabled")
                if text.strip():
                    print(f"  {i+1}. '{text.strip()}' disabled={disabled is not None}")

            # Suche nach Uhrzeiten
            print("\nSuche nach Uhrzeiten...")
            times = ["16:00", "16:15", "16:30", "17:00", "17:15", "17:30", "18:00", "18:15", "18:30", "19:00", "19:15", "19:30"]
            for t in times:
                try:
                    slot = page.get_by_text(t, exact=True).first
                    if await slot.is_visible(timeout=1000):
                        print(f"  {t}: SICHTBAR")
                    else:
                        print(f"  {t}: nicht sichtbar")
                except:
                    print(f"  {t}: Fehler")

            # Suche nach allen Elementen mit Zeit-Format
            print("\nSuche nach allen Zeit-Elementen...")
            all_elements = await page.query_selector_all("td, div, span")
            for el in all_elements:
                text = await el.text_content() or ""
                if ":" in text:
                    print(f"  Zeit gefunden: '{text}'")

            # Warte länger und prüfe erneut
            print("\nWarte 5 Sekunden und pruefe erneut...")
            await page.wait_for_timeout(5000)

            print("\nButtons nach Warten:")
            buttons = await page.query_selector_all("button, [role='button']")
            for i, btn in enumerate(buttons):
                text = await btn.text_content() or ""
                cls = await btn.get_attribute("class") or ""
                disabled = await btn.get_attribute("disabled")
                if text.strip():
                    print(f"  {i+1}. '{text.strip()}' disabled={disabled is not None}")

            await page.screenshot(path="screenshots/check_after_wait.png")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
