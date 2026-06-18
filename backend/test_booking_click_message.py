"""
Test-Skript: Buchung mit explizitem Klick auf Nachricht-Feld vor dem Ausfüllen
"""
import asyncio
import logging
from datetime import datetime
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Test-Daten - angepasst für Resmio Widget
TEST_DETAIL_URL = "https://app.resmio.com/pension-schmidt/widget?backgroundColor=%23555555&color=%23ffffff&commentsDisabled=false&facebookLogin=false&fontSize=18px&fullscreen=true&height=400&linkBackgroundColor=%23c44707&newsletterSignup=false&width=275"
TEST_EVENT_DATE = datetime(2026, 6, 10)
TEST_GUESTS = 4
TEST_MESSAGE = "Diese Buchung wurde von einer KI fuer mich durchgefuehrt. Bei Problemen bitte anrufen!!"


async def main():
    logger.info("Starte Buchungstest mit Klick-auf-Nachricht-Feld")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # headless=False um den Prozess zu sehen
        context = await browser.new_context(locale="de-DE")
        page = await context.new_page()

        try:
            # 1. Direkt zum Resmio Widget
            logger.info(f"Gehe zu Resmio Widget: {TEST_DETAIL_URL}")
            await page.goto(TEST_DETAIL_URL, wait_until="networkidle", timeout=30000)
            await page.screenshot(path="screenshots/test_click_01_widget.png")

            # Widget ist direkt geladen
            ctx = page
            logger.info("Resmio Widget direkt geladen")

            await ctx.wait_for_timeout(3000)
            await page.screenshot(path="screenshots/test_click_02_widget_loaded.png")
            logger.info("Screenshot nach Widget-Load gespeichert")

            # Debug: Alle Input-Felder auflisten
            inputs = await ctx.query_selector_all("input, textarea, select")
            logger.info(f"Gefundene Input-Elemente: {len(inputs)}")
            for i, inp in enumerate(inputs):
                try:
                    tag = await inp.evaluate("el => el.tagName.toLowerCase()")
                    placeholder = await inp.evaluate("el => el.placeholder || ''")
                    name = await inp.evaluate("el => el.name || ''")
                    type_ = await inp.evaluate("el => el.type || ''")
                    logger.info(f"  Input {i}: <{tag}> name='{name}' type='{type_}' placeholder='{placeholder}'")
                except:
                    pass

            # 3. Im Widget: Datum/Uhrzeit auswählen
            # Resmio Widget zeigt oft Kalender-Grid mit Daten und Uhrzeiten als Buttons
            await ctx.wait_for_timeout(2000)
            await page.screenshot(path="screenshots/test_click_03_widget_state.png")
            logger.info("Screenshot: aktueller Widget-Status")

            # Zuerst prüfen, ob ein "Weiter"/"Next" Button vorhanden ist (wir sind schon auf Seite 2)
            # Oder wir müssen erst Datum/Uhrzeit wählen

            # Versuche: Uhrzeiten im Widget finden (19:00, 19:15, 19:30)
            chosen = None
            for t in ["19:30", "19:15", "19:00", "19:00 Uhr", "19:15 Uhr", "19:30 Uhr"]:
                try:
                    time_btn = ctx.get_by_text(t, exact=False).first
                    if await time_btn.is_visible(timeout=1500):
                        disabled = await time_btn.get_attribute("disabled")
                        if disabled is None:
                            await time_btn.click()
                            chosen = t
                            logger.info(f"Uhrzeit gewählt: {t}")
                            await ctx.wait_for_timeout(1000)
                            break
                except:
                    pass

            if not chosen:
                logger.warning("Keine verfügbare Uhrzeit im Widget gefunden")
                await page.screenshot(path="screenshots/test_click_04_no_time.png")
                return

            await page.screenshot(path="screenshots/test_click_05_time_selected.png")
            logger.info("Schritt 4: Uhrzeit gewählt")

            # 5. Kontaktdaten ausfüllen (Seite 2 des Widgets)
            await ctx.wait_for_timeout(1500)
            await page.screenshot(path="screenshots/test_click_06_contact_page.png")
            logger.info("Screenshot: Kontaktseite")

            # Name
            for selector in ("input[name='name']", "input[placeholder*='Name']", "input[id*='name']"):
                try:
                    inp = ctx.locator(selector).first
                    if await inp.is_visible(timeout=2000):
                        await inp.click()
                        await inp.fill("Test User", timeout=3000)
                        logger.info("Name ausgefüllt")
                        break
                except:
                    pass

            # Email
            for selector in ("input[type='email']", "input[name='email']", "input[id*='email']"):
                try:
                    inp = ctx.locator(selector).first
                    if await inp.is_visible(timeout=2000):
                        await inp.click()
                        await inp.fill("test@example.com", timeout=3000)
                        logger.info("Email ausgefüllt")
                        break
                except:
                    pass

            # Telefon (optional)
            for selector in ("input[type='tel']", "input[name='phone']", "input[id*='phone']"):
                try:
                    inp = ctx.locator(selector).first
                    if await inp.is_visible(timeout=2000):
                        await inp.click()
                        await inp.fill("0123456789", timeout=3000)
                        logger.info("Telefon ausgefüllt")
                        break
                except:
                    pass

            await page.screenshot(path="screenshots/test_click_07_contacts_filled.png")

            # 6. **WICHTIG**: Nachricht-Feld finden - erst klicken, dann füllen!
            logger.info("Suche Nachricht-Feld (textarea oder input)...")
            message_found = False

            # Alle Textarea- und Input-Felder auflisten für Debugging
            all_texts = await ctx.query_selector_all("textarea, input[type='text'], input[name='message'], input[name='note']")
            logger.info(f"Gefundene Text-Felder: {len(all_texts)}")
            for i, field in enumerate(all_texts):
                try:
                    placeholder = await field.evaluate("el => el.placeholder || ''")
                    name = await field.evaluate("el => el.name || ''")
                    logger.info(f"  Field {i}: name='{name}' placeholder='{placeholder}'")
                except:
                    pass

            # Suche nach Nachricht-Feld mit verschiedenen Selectoren
            for selector in (
                "textarea[name='message']", "textarea[name='note']", "textarea[placeholder*='Nachricht']", "textarea[placeholder*='Kommentar']",
                "input[name='message']", "input[name='note']",
                "[placeholder*='Nachricht']", "[placeholder*='message']", "[placeholder*='Kommentar']", "[placeholder*='Anmerkung']",
                "textarea"  # Fallback: erstes textarea
            ):
                try:
                    msg_inp = ctx.locator(selector).first
                    if await msg_inp.is_visible(timeout=1500):
                        logger.info(f"Nachricht-Feld gefunden mit: {selector}")

                        # ***EXPLIZIT HINEINKLICKEN*** - das ist der wichtige Schritt!
                        logger.info("Klicke IN das Nachricht-Feld (vor dem Ausfüllen)...")
                        await msg_inp.scroll_into_view()
                        await ctx.wait_for_timeout(500)
                        await msg_inp.click(force=True)
                        await ctx.wait_for_timeout(1000)

                        # Jetzt erst füllen
                        logger.info("Fülle Nachricht-Feld mit Test-Nachricht...")
                        await msg_inp.fill(TEST_MESSAGE, timeout=3000)

                        # Verifizieren
                        value = await msg_inp.input_value(timeout=2000)
                        logger.info(f"Nachricht-Feld Inhalt: '{value[:50]}...'")

                        message_found = True
                        break
                except Exception as e:
                    logger.warning(f"Selector '{selector}' fehlgeschlagen: {e}")
                    continue

            if not message_found:
                logger.warning("Nachricht-Feld nicht gefunden - suche alle textarea/input Felder")
                # Fallback: jedes Textarea anklicken und testen
                textareas = await ctx.query_selector_all("textarea")
                for i, ta in enumerate(textareas):
                    try:
                        await ta.scroll_into_view()
                        await ta.click(force=True)
                        await ctx.wait_for_timeout(500)
                        await ta.fill("TEST - Klick funktioniert!", timeout=2000)
                        val = await ta.input_value()
                        logger.info(f"Textarea {i} funktioniert: '{val}'")
                        if "TEST" in val:
                            logger.info("✓ Textarea-Klick erfolgreich!")
                            break
                    except Exception as e:
                        logger.warning(f"Textarea {i} fehlgeschlagen: {e}")

            await page.screenshot(path="screenshots/test_click_08_message_field.png")
            logger.info("Screenshot: Nachricht-Feld Status")

            # 8. STOPP vor Confirm - nur testen, dass alles ausgefüllt ist
            logger.info("STOPP vor Confirm-Button - Test erfolgreich!")
            logger.info("Manuell prüfen: Alle Felder ausgefüllt? Dann 'Weiter'/Confirm klicken.")

            # Warten auf manuelle Interaktion
            await page.wait_for_timeout(60000)  # 60 Sekunden warten

        except Exception as e:
            logger.error(f"Fehler: {e}")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
