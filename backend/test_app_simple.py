"""
Einfache Testausfuehrung - alle Testfaelle ohne Unicode-Probleme
"""
import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

URL = "https://www.pensionschmidt.se/programm/quizquizbangbang202411-cz495-67pmf-9bsrg-2s8ss-3l54z-5xr97-rjsx2-9ex4j-hd5za-cj2lt-8k5hs"
RESULTS = []

def log_test(tc_id, name, status, msg=""):
    RESULTS.append({
        "tc_id": tc_id, "name": name, "status": status, "message": msg
    })
    s = "PASS" if status == "PASS" else "FAIL" if status == "FAIL" else "SKIP"
    print("[%s] %s: %s" % (s, tc_id, name))
    if msg:
        print("      >> %s" % msg)

async def tc001():
    """TC-001: Gültiges Datum setzen"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(locale="de-DE")
            page = await context.new_page()

            await page.goto(URL, wait_until="networkidle", timeout=30000)

            async with context.expect_page(timeout=8000) as popup_info:
                await page.get_by_text("Reservieren", exact=False).first.click()
            popup = await popup_info.value
            await popup.wait_for_load_state("domcontentloaded")
            await popup.wait_for_timeout(2000)

            date_picker = popup.locator(".date-picker").first
            await date_picker.click()
            await popup.wait_for_timeout(2000)

            cells = await popup.locator(".datepicker-cell").all()
            found = False
            for cell in cells:
                text = await cell.text_content() or ""
                if text.strip() == "25":
                    cls = await cell.get_attribute("class") or ""
                    if "is-unselectable" not in cls:
                        await cell.click()
                        found = True
                        break

            await browser.close()
            log_test("TC-001", "Gültiges Datum setzen", "PASS" if found else "FAIL",
                    "Tag 25 erfolgreich" if found else "Tag 25 nicht gefunden")
    except Exception as e:
        log_test("TC-001", "Gültiges Datum setzen", "FAIL", str(e)[:50])

async def tc002():
    """TC-002: Ungültiges Datum (is-unselectable)"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(locale="de-DE")
            page = await context.new_page()

            await page.goto(URL, wait_until="networkidle", timeout=30000)

            async with context.expect_page(timeout=8000) as popup_info:
                await page.get_by_text("Reservieren", exact=False).first.click()
            popup = await popup_info.value
            await popup.wait_for_load_state("domcontentloaded")
            await popup.wait_for_timeout(2000)

            date_picker = popup.locator(".date-picker").first
            await date_picker.click()
            await popup.wait_for_timeout(2000)

            cells = await popup.locator(".datepicker-cell").all()
            found_unselectable = False
            for cell in cells:
                text = await cell.text_content() or ""
                if text.strip() == "01":
                    cls = await cell.get_attribute("class") or ""
                    if "is-unselectable" in cls:
                        found_unselectable = True
                    break

            await browser.close()
            log_test("TC-002", "Ungültiges Datum (is-unselectable)", "PASS" if found_unselectable else "FAIL",
                    "Tag 01 ist unselectable" if found_unselectable else "Tag 01 nicht unselectable")
    except Exception as e:
        log_test("TC-002", "Ungültiges Datum (is-unselectable)", "FAIL", str(e)[:50])

async def tc004():
    """TC-004: 4 Gäste setzen"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(locale="de-DE")
            page = await context.new_page()

            await page.goto(URL, wait_until="networkidle", timeout=30000)

            async with context.expect_page(timeout=8000) as popup_info:
                await page.get_by_text("Reservieren", exact=False).first.click()
            popup = await popup_info.value
            await popup.wait_for_load_state("domcontentloaded")
            await popup.wait_for_timeout(2000)

            # Datum
            date_picker = popup.locator(".date-picker").first
            await date_picker.click()
            await popup.wait_for_timeout(2000)

            cells = await popup.locator(".datepicker-cell").all()
            for cell in cells:
                text = await cell.text_content() or ""
                if text.strip() == "25":
                    cls = await cell.get_attribute("class") or ""
                    if "is-unselectable" not in cls:
                        await cell.click()
                        break

            await popup.keyboard.press("Escape")
            await popup.wait_for_timeout(1000)

            # Gäste
            guest_picker = popup.locator(".guest-picker").first
            await guest_picker.click()
            await popup.wait_for_timeout(1500)

            variants = ["4 Gäste", "4 Gaste", "4 Guests", "4 Gast"]
            found = False
            for variant in variants:
                try:
                    option = popup.get_by_text(variant, exact=False).first
                    if await option.is_visible(timeout=500):
                        await option.click()
                        found = True
                        await popup.wait_for_timeout(1000)
                        await popup.keyboard.press("Escape")
                        await popup.wait_for_timeout(1000)
                        break
                except:
                    continue

            await browser.close()
            log_test("TC-004", "4 Gäste setzen", "PASS" if found else "FAIL",
                    "Gäste-Option gefunden" if found else "Keine Variante gefunden")
    except Exception as e:
        log_test("TC-004", "4 Gäste setzen", "FAIL", str(e)[:50])

async def tc008():
    """TC-008: Slot mit cursor=pointer ist buchbar"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(locale="de-DE")
            page = await context.new_page()

            await page.goto(URL, wait_until="networkidle", timeout=30000)

            async with context.expect_page(timeout=8000) as popup_info:
                await page.get_by_text("Reservieren", exact=False).first.click()
            popup = await popup_info.value
            await popup.wait_for_load_state("domcontentloaded")
            await popup.wait_for_timeout(2000)

            # Datum
            date_picker = popup.locator(".date-picker").first
            await date_picker.click()
            await popup.wait_for_timeout(2000)

            cells = await popup.locator(".datepicker-cell").all()
            for cell in cells:
                text = await cell.text_content() or ""
                if text.strip() == "25":
                    cls = await cell.get_attribute("class") or ""
                    if "is-unselectable" not in cls:
                        await cell.click()
                        break

            await popup.keyboard.press("Escape")
            await popup.wait_for_timeout(1000)

            # Gäste: 2
            guest_picker = popup.locator(".guest-picker").first
            await guest_picker.click()
            await popup.wait_for_timeout(1500)

            for variant in ["2 Gäste", "2 Gaste", "2 Guests"]:
                try:
                    option = popup.get_by_text(variant, exact=False).first
                    if await option.is_visible(timeout=500):
                        await option.click()
                        await popup.wait_for_timeout(1000)
                        await popup.keyboard.press("Escape")
                        await popup.wait_for_timeout(1000)
                        break
                except:
                    continue

            # Slot prüfen
            await popup.wait_for_timeout(2000)
            slot = popup.get_by_text("19:00", exact=True).first

            if await slot.is_visible(timeout=1000):
                cursor = await slot.evaluate("el => window.getComputedStyle(el).cursor")
                slot_text = await slot.text_content() or ""
                has_not_available = "not available" in slot_text.lower()

                is_bookable = cursor == "pointer" and not has_not_available
                log_test("TC-008", "Slot cursor=pointer ist buchbar", "PASS" if is_bookable else "FAIL",
                        "19:00 buchbar (cursor=%s)" % cursor)
            else:
                log_test("TC-008", "Slot cursor=pointer ist buchbar", "SKIP", "19:00 nicht sichtbar")

            await browser.close()
    except Exception as e:
        log_test("TC-008", "Slot cursor=pointer ist buchbar", "FAIL", str(e)[:50])

async def tc009():
    """TC-009: Slot mit cursor=not-allowed ist nicht buchbar"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(locale="de-DE")
            page = await context.new_page()

            await page.goto(URL, wait_until="networkidle", timeout=30000)

            async with context.expect_page(timeout=8000) as popup_info:
                await page.get_by_text("Reservieren", exact=False).first.click()
            popup = await popup_info.value
            await popup.wait_for_load_state("domcontentloaded")
            await popup.wait_for_timeout(2000)

            # Datum
            date_picker = popup.locator(".date-picker").first
            await date_picker.click()
            await popup.wait_for_timeout(2000)

            cells = await popup.locator(".datepicker-cell").all()
            for cell in cells:
                text = await cell.text_content() or ""
                if text.strip() == "25":
                    cls = await cell.get_attribute("class") or ""
                    if "is-unselectable" not in cls:
                        await cell.click()
                        break

            await popup.keyboard.press("Escape")
            await popup.wait_for_timeout(1000)

            # Gäste: 4
            guest_picker = popup.locator(".guest-picker").first
            await guest_picker.click()
            await popup.wait_for_timeout(1500)

            for variant in ["4 Gäste", "4 Gaste", "4 Guests"]:
                try:
                    option = popup.get_by_text(variant, exact=False).first
                    if await option.is_visible(timeout=500):
                        await option.click()
                        await popup.wait_for_timeout(1000)
                        await popup.keyboard.press("Escape")
                        await popup.wait_for_timeout(1000)
                        break
                except:
                    continue

            # Slot prüfen
            await popup.wait_for_timeout(2000)
            slot = popup.get_by_text("19:15", exact=True).first

            if await slot.is_visible(timeout=1000):
                cursor = await slot.evaluate("el => window.getComputedStyle(el).cursor")
                is_not_bookable = cursor == "not-allowed"
                log_test("TC-009", "Slot cursor=not-allowed ist nicht buchbar", "PASS" if is_not_bookable else "FAIL",
                        "19:15 nicht buchbar (cursor=%s)" % cursor)
            else:
                log_test("TC-009", "Slot cursor=not-allowed ist nicht buchbar", "SKIP", "19:15 nicht sichtbar")

            await browser.close()
    except Exception as e:
        log_test("TC-009", "Slot cursor=not-allowed ist nicht buchbar", "FAIL", str(e)[:50])

async def main():
    print("\n" + "="*70)
    print("TEST-AUSFUEHRUNG - Alle Testfaelle")
    print("="*70 + "\n")

    print("Kategorie 1: Datum-Setzung\n")
    await tc001()
    await tc002()

    print("\nKategorie 2: Gäste-Anzahl\n")
    await tc004()

    print("\nKategorie 3: Slot-Verfuegbarkeit\n")
    await tc008()
    await tc009()

    # Statistik
    passed = len([r for r in RESULTS if r["status"] == "PASS"])
    failed = len([r for r in RESULTS if r["status"] == "FAIL"])
    skipped = len([r for r in RESULTS if r["status"] == "SKIP"])

    print("\n" + "="*70)
    print("ERGEBNISSE")
    print("="*70)
    print("BESTANDEN: %d" % passed)
    print("FEHLGESCHLAGEN: %d" % failed)
    print("UEBERSPRUNGEN: %d" % skipped)
    print("GESAMT: %d\n" % len(RESULTS))

    # Speichern
    with open("test_results.json", "w") as f:
        json.dump(RESULTS, f, indent=2, ensure_ascii=False)

    print("Ergebnisse gespeichert: test_results.json")

if __name__ == "__main__":
    asyncio.run(main())
