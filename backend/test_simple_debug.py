#!/usr/bin/env python3
"""
Debug: Zeige das gesamte HTML nach dem Öffnen des Datumpickers
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
            await page.screenshot(path="screenshots/debug_01_detailseite.png")

            # Resmio öffnen
            async with context.expect_page(timeout=8000) as popup_info:
                await page.get_by_text("Reservieren", exact=False).first.click()
            page = await popup_info.value
            await page.wait_for_load_state("networkidle", timeout=20000)
            await page.wait_for_timeout(2000)
            await page.screenshot(path="screenshots/debug_02_resmio_open.png")

            # Datum-Picker öffnen
            await page.get_by_text("Heute", exact=True).first.click()
            await page.wait_for_timeout(3000)
            await page.screenshot(path="screenshots/debug_03_picker_open.png")

            # HTML ausgeben
            html = await page.content()

            # Einfache Suche nach Tagen
            print("Suche nach Tageszahlen im HTML...")
            import re
            days = re.findall(r'>([0-9]{1,2})<', html)
            unique_days = sorted(set(int(d) for d in days if int(d) <= 31))
            print(f"Tage im HTML: {unique_days}")

            # Suche nach "Juni" oder "Juni 2026"
            if "Juni" in html:
                print("Juni wurde im HTML gefunden!")
            if "2026" in html:
                print("2026 wurde im HTML gefunden!")

            # Alle Buttons auflisten
            print("\nAlle Buttons:")
            buttons = await page.query_selector_all("button, [role='button']")
            for i, btn in enumerate(buttons[:15]):  # Nur erste 15
                text = await btn.text_content() or ""
                cls = await btn.get_attribute("class") or ""
                print(f"  {i+1}. '{text.strip()}' class='{cls}'")

            # Alle td Elemente (Kalender-Tage)
            print("\nAlle td Elemente mit Text:")
            tds = await page.query_selector_all("td")
            for i, td in enumerate(tds[:20]):
                text = await td.text_content() or ""
                cls = await td.get_attribute("class") or ""
                if text.strip():
                    print(f"  td: text='{text.strip()}' class='{cls}'")

            await page.screenshot(path="screenshots/debug_04_full_page.png")
            print("\nScreenshots gespeichert:")
            print("  - debug_01_detailseite.png")
            print("  - debug_02_resmio_open.png")
            print("  - debug_03_picker_open.png")
            print("  - debug_04_full_page.png")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
