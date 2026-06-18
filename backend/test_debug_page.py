#!/usr/bin/env python3
"""
Debug: Zeige alle Eingabefelder und Buttons auf der Seite an
"""

import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

async def main():
    detail_url = "https://www.pensionschmidt.se/programm/verquizmeinnicht-trp7e-5z68l-5rldg-x3wkr-gc3dy-fa7hc-mk4hb-97dbl-3a4be"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(locale="de-DE")
        page = await context.new_page()

        try:
            await page.goto(detail_url, wait_until="networkidle", timeout=30000)
            print("Seite geladen!")

            # Auf "Reservieren" klicken
            for btn_text in ("Reservieren", "Buchen", "Reserve", "Book"):
                btn = page.get_by_text(btn_text, exact=False).first
                try:
                    if await btn.is_visible(timeout=3000):
                        print(f"Button '{btn_text}' gefunden!")
                        async with context.expect_page(timeout=6000) as popup_info:
                            await btn.click()
                        popup = await popup_info.value
                        await popup.wait_for_load_state("networkidle", timeout=20000)
                        print(f"Resmio Popup geoeffnet: {popup.url}")
                        page = popup
                        break
                except Exception as e:
                    print(f"Button '{btn_text}' nicht sichtbar: {e}")
                    continue

            await page.wait_for_timeout(3000)

            # Alle Input-Felder auflisten
            print("\n" + "="*60)
            print("ALLE INPUT-FELDER AUF DER SEITE:")
            print("="*60)

            inputs = await page.query_selector_all("input, textarea, select")
            for i, inp in enumerate(inputs):
                tag = await inp.evaluate("el => el.tagName.toLowerCase()")
                type_attr = await inp.get_attribute("type") or ""
                name = await inp.get_attribute("name") or ""
                placeholder = await inp.get_attribute("placeholder") or ""
                class_attr = await inp.get_attribute("class") or ""
                id_attr = await inp.get_attribute("id") or ""
                print(f"{i+1}. <{tag} type='{type_attr}' name='{name}' placeholder='{placeholder}' class='{class_attr}' id='{id_attr}'>")

            # Alle Buttons auflisten
            print("\n" + "="*60)
            print("ALLE BUTTONS AUF DER SEITE:")
            print("="*60)

            buttons = await page.query_selector_all("button, [role='button']")
            for i, btn in enumerate(buttons):
                text = await btn.text_content() or ""
                role = await btn.get_attribute("role") or ""
                class_attr = await btn.get_attribute("class") or ""
                print(f"{i+1}. <button> text='{text.strip()}' role='{role}' class='{class_attr}'>")

            # Screenshots speichern
            import os
            os.makedirs("screenshots", exist_ok=True)
            await page.screenshot(path="screenshots/debug_full_page.png")
            print("\nScreenshot gespeichert: screenshots/debug_full_page.png")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
