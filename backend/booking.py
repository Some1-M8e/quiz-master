import logging
import os
from datetime import datetime
from config import settings

logger = logging.getLogger(__name__)

TARGET_SLOTS = ["19:30", "19:15", "19:00"]  # Späteste zuerst, um späteste verfügbare zu wählen


async def _open_resmio(page, browser_context):
    """Klickt auf Reservieren und gibt den Kontext zurück, in dem Resmio geladen ist."""
    for btn_text in ("Reservieren", "Buchen", "Reserve", "Book"):
        btn = page.get_by_text(btn_text, exact=False).first
        try:
            if not await btn.is_visible(timeout=3000):
                continue
            # Popup abfangen (Resmio öffnet oft in neuem Tab)
            async with browser_context.expect_page(timeout=6000) as popup_info:
                await btn.click()
            popup = await popup_info.value
            await popup.wait_for_load_state("networkidle", timeout=20000)
            # Warte auf Widget-Inhalt
            await popup.wait_for_timeout(5000)
            logger.info(f"Resmio als Popup geladen: {popup.url}")
            return popup
        except Exception:
            # Kein Popup — vielleicht iframe oder inline
            try:
                await btn.click(timeout=5000)
                break
            except Exception:
                continue

    await page.wait_for_timeout(3000)

    # Iframe prüfen
    for frame in page.frames:
        if "resmio" in frame.url.lower():
            logger.info(f"Resmio als iframe gefunden: {frame.url}")
            # Warte auf Iframe-Inhalt
            try:
                await frame.wait_for_load_state("domcontentloaded", timeout=10000)
                await frame.wait_for_timeout(3000)
            except Exception:
                pass
            return frame

    logger.info("Resmio nicht als Popup/iframe gefunden — nutze Hauptseite")
    return page


async def _set_date(ctx, event_date: datetime) -> bool:
    date_iso = event_date.strftime("%Y-%m-%d")
    date_de = event_date.strftime("%d.%m.%Y")

    # Mehr Wartezeit nach Resmio-Öffnung
    await ctx.wait_for_timeout(4000)

    # Helper: Versuche Datum in einem Context (Page oder Frame) zu setzen
    async def try_set_date_in_context(c, ctx_name: str) -> bool:
        logger.info(f"DEBUG {ctx_name}: Suche Datum-Input, suche alle Inputs...")
        # Debug: Alle Inputs auflisten
        try:
            all_inputs = await c.query_selector_all("input")
            logger.info(f"DEBUG {ctx_name}: Gefundene Inputs: {[await i.get_attribute('type') for i in all_inputs[:10]]}")
        except Exception as e:
            logger.info(f"DEBUG {ctx_name}: Cannot list inputs: {e}")

        # 1. HTML5 date input
        try:
            inp = c.locator("input[type='date']").first
            await inp.wait_for(state="visible", timeout=3000)
            await inp.fill(date_iso)
            await inp.press("Tab")
            logger.info(f"Datum gesetzt ({ctx_name}, HTML5): {date_iso}")
            return True
        except TimeoutError:
            logger.info(f"DEBUG {ctx_name}: Kein HTML5 date input sichtbar")
            pass
        except Exception as e:
            logger.debug(f"{ctx_name} HTML5 date input Fehler: {type(e).__name__}")

        # 2. Text-Input mit explizitem Timeout-Check
        for selector in ["input[placeholder*='Datum']", "input[placeholder*='date']"]:
            try:
                inp = c.locator(selector).first
                if await inp.is_visible(timeout=2000):
                    await inp.triple_click()
                    await inp.fill(date_de)
                    await inp.press("Tab")
                    logger.info(f"Datum gesetzt ({ctx_name}, Text mit Placeholder): {date_de}")
                    return True
            except TimeoutError:
                continue

        # 3. JavaScript - HTML-Inhalt und alle Elemente auslesen
        try:
            # Erst den gesamten HTML-Inhalt loggen
            html = await c.evaluate("() => document.body.innerHTML")
            logger.info(f"DEBUG {ctx_name} HTML-Inhalt (erste 1000 Zeichen): {html[:1000] if html else 'EMPTY'}")

            # Alle Elemente auflisten
            all_tags = await c.evaluate("() => [...document.querySelectorAll('*')].map(e => e.tagName).filter((t,i,a)=>!a.includes(t,i+1))")
            logger.info(f"DEBUG {ctx_name} Alle Tags im Dokument: {all_tags}")

            # Dann versuchen, Inputs zu setzen
            js_code = f"""() => {{
                const inputs = document.querySelectorAll('input[type="date"], input[type="text"]');
                console.log('Found inputs:', inputs.length);
                for (let inp of inputs) {{
                    console.log('Checking inp:', inp.type, inp.placeholder, inp.offsetParent);
                    if (inp.offsetParent !== null) {{
                        inp.value = '{date_iso}';
                        inp.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        console.log('Set date via JS');
                        return true;
                    }}
                }}
                return false;
            }}"""
            result = await c.evaluate(js_code)
            logger.info(f"DEBUG {ctx_name} JS-Ergebnis: {result}")
            if result:
                logger.info(f"Datum per JavaScript gesetzt ({ctx_name}): {date_iso}")
                await c.wait_for_timeout(1000)
                return True
        except Exception as e:
            logger.info(f"DEBUG {ctx_name} JS-Datum fehlgeschlagen: {e}")

        return False

    # ctx ist entweder eine Page (Popup) oder ein Frame
    # Prüfen ob es ein Frame ist (hat keine wait_for_timeout Methode)
    if hasattr(ctx, 'wait_for_timeout'):
        # Es ist eine Page
        if await try_set_date_in_context(ctx, "Page"):
            return True
        # Versuche in allen Frames
        for i, frame in enumerate(ctx.frames):
            if 'resmio' in frame.url.lower():
                logger.info(f"Resmio Iframe #{i} gefunden: {frame.url}")
                if await try_set_date_in_context(frame, f"Frame[{i}]"):
                    return True
    else:
        # Es ist direkt ein Frame
        if await try_set_date_in_context(ctx, "Frame"):
            return True

    logger.error(f"Konnte Datum {date_de} nicht setzen")
    return False


async def _set_guests(ctx, count: int = 4) -> bool:
    try:
        sel = ctx.locator("select").first
        await sel.wait_for(state="visible", timeout=5000)
        await sel.select_option(str(count))
        return True
    except TimeoutError:
        logger.debug("Select-Element nicht sichtbar, versuche Stepper")
    except Exception as e:
        logger.debug(f"Fehler bei Select: {type(e).__name__}")

    try:
        plus = ctx.get_by_role("button", name="+").first
        current_el = ctx.locator("[data-guests],[data-count],[aria-valuetext]").first
        current = int(await current_el.text_content(timeout=3000) or "1")
        for _ in range(count - current):
            await plus.click()
        return True
    except TimeoutError:
        logger.warning("Stepper-Button nicht sichtbar")
    except Exception as e:
        logger.warning(f"Fehler bei Stepper: {type(e).__name__}: {e}")

    return False


async def _available_slots(ctx) -> list[str]:
    """Gibt verfügbare Uhrzeiten zwischen 19:00 und 19:30 zurück (späteste zuerst)."""
    await ctx.wait_for_timeout(2500)
    available = []
    for t in TARGET_SLOTS:
        try:
            slot = ctx.get_by_text(t, exact=True).first
            if not await slot.is_visible(timeout=2000):
                continue
            disabled = await slot.get_attribute("disabled")
            aria_disabled = await slot.get_attribute("aria-disabled")
            cls = await slot.get_attribute("class") or ""
            if disabled is None and aria_disabled != "true" and "disabled" not in cls and "full" not in cls:
                available.append(t)
        except Exception:
            pass
    return available


async def check_bookable(detail_url: str, event_date: datetime) -> bool:
    """Prüft ob ein Termin 19:00–19:30 Uhr mit 4 Personen buchbar ist (ohne zu buchen)."""
    result = await _check_slots(detail_url, event_date)
    return result >= 4  # True nur wenn 4+ Plätze verfügbar → Termin ist buchbar

async def check_partial_bookable(detail_url: str, event_date: datetime) -> int:
    """Prüft wie viele Plätze (2-4) verfügbar sind. Gibt Anzahl zurück oder 0 wenn nichts buchbar."""
    return await _check_slots(detail_url, event_date)

async def _check_slots(detail_url: str, event_date: datetime) -> int:
    """Interne Funktion: prüft Slots für 4, 3, 2 Personen und gibt maximale buchbare Anzahl zurück."""
    if settings.booking_dry_run:
        logger.info(f"[DRY-RUN] Buchbarkeitsprüfung übersprungen für {detail_url}")
        return 4  # Dry-Run: immer als voll betrachten

    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(locale="de-DE")
        page = await context.new_page()
        try:
            await page.goto(detail_url, wait_until="networkidle", timeout=30000)
            os.makedirs("screenshots", exist_ok=True)
            await page.screenshot(path=f"screenshots/check_1_{event_date.strftime('%Y%m%d')}.png")

            ctx = await _open_resmio(page, context)
            await page.screenshot(path=f"screenshots/check_2_{event_date.strftime('%Y%m%d')}.png")

            await _set_date(ctx, event_date)

            # Prüfe für 4, 3, 2 Personen – welche ist die maximale buchbare Anzahl?
            for persons in [4, 3, 2]:
                await _set_guests(ctx, persons)
                await ctx.wait_for_timeout(1500)
                slots = await _available_slots(ctx)
                if slots:
                    logger.info(f"Verfügbare Slots für {event_date.strftime('%d.%m.%Y')} ({persons} Personen): {slots}")
                    return persons

            logger.info(f"Keine freien Slots 19:00–19:30 für {event_date.strftime('%d.%m.%Y')} (auch nicht für 2 Personen)")
            return 0
        except Exception as e:
            logger.error(f"Buchbarkeitsprüfung fehlgeschlagen ({detail_url}): {e}")
            return 0
        finally:
            await browser.close()


async def book_event(detail_url: str, event_date: datetime, event_title: str = "", dry_run: bool = False, stop_before_confirm: bool = False, custom_guests: int = None) -> bool:
    if settings.booking_dry_run or dry_run:
        label = event_title or detail_url
        logger.info(f"[DRY-RUN] Würde buchen: {label} am {event_date.strftime('%d.%m.%Y')}")
        return True

    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(locale="de-DE")
        page = await context.new_page()
        try:
            await page.goto(detail_url, wait_until="networkidle", timeout=30000)
            await page.screenshot(path="screenshots/test_01_seite_geladen.png")
            logger.info("Schritt 1: Detailseite geladen")

            ctx = await _open_resmio(page, context)
            await page.screenshot(path="screenshots/test_02_resmio_geoeffnet.png")
            logger.info("Schritt 2: Resmio geoeffnet")

            if not await _set_date(ctx, event_date):
                logger.error("Datum konnte nicht gesetzt werden")
                return False
            await page.screenshot(path="screenshots/test_03_datum_gesetzt.png")
            logger.info(f"Schritt 3: Datum gesetzt auf {event_date.strftime('%d.%m.%Y')}")

            # Benutzerspezifische Personenzahl
            guests = custom_guests if custom_guests is not None else 4
            if not await _set_guests(ctx, guests):
                logger.error("Personenzahl konnte nicht gesetzt werden")
                return False
            await page.screenshot(path="screenshots/test_04_personen_gesetzt.png")
            logger.info(f"Schritt 4: Personen gesetzt auf {guests}")

            await ctx.wait_for_timeout(2000)
            slots = await _available_slots(ctx)
            if not slots:
                logger.info(f"Keine freien Slots 19:00–19:30 für {event_date.strftime('%d.%m.%Y')}")
                return False
            logger.info(f"Verfügbare Slots: {slots}")

            # Späteste verfügbare Uhrzeit wählen
            chosen = slots[0]
            await ctx.get_by_text(chosen, exact=True).first.click(timeout=5000)
            await ctx.wait_for_timeout(2000)
            await page.screenshot(path="screenshots/test_05_uhrzeit_gewaehlt.png")
            logger.info(f"Schritt 5: Uhrzeit gewählt: {chosen}")

            # Kontaktdaten ausfüllen
            for selector in ("input[name='name']", "input[placeholder*='Name']", "input[placeholder*='name']"):
                try:
                    await ctx.locator(selector).first.fill(settings.organizer_name, timeout=3000)
                    break
                except Exception:
                    pass
            for selector in ("input[type='email']", "input[name='email']"):
                try:
                    await ctx.locator(selector).first.fill(settings.organizer_email, timeout=3000)
                    break
                except Exception:
                    pass
            if settings.organizer_phone:
                for selector in ("input[type='tel']", "input[name='phone']", "input[name='telephone']"):
                    try:
                        await ctx.locator(selector).first.fill(settings.organizer_phone, timeout=3000)
                        break
                    except Exception:
                        pass
            await page.screenshot(path="screenshots/test_06_kontaktdaten_ausgefuellt.png")
            logger.info("Schritt 6: Kontaktdaten ausgefüllt")

            # Optionale Nachricht eintragen
            for selector in ("textarea", "input[name='message']", "input[name='note']", "[placeholder*='Nachricht']", "[placeholder*='message']", "[placeholder*='Anmerkung']"):
                try:
                    msg_inp = ctx.locator(selector).first
                    if await msg_inp.is_visible(timeout=2000):
                        await msg_inp.fill("Diese Buchung wurde von einer KI für mich durchgeführt. Bei Problemen bitte anrufen!!", timeout=3000)
                        logger.info("Nachricht im Buchungformular eingetragen")
                        break
                except Exception:
                    pass

            await page.screenshot(path="screenshots/test_07_nachricht_eingetragen.png")
            logger.info("Schritt 7: Nachricht eingetragen")

            if stop_before_confirm:
                logger.info("STOPP vor Confirm-Button (Testmodus)")
                await page.screenshot(path="screenshots/test_08_vor_confirm_stopp.png")
                logger.info("Test abgeschlossen - alle Felder ausgefüllt, Confirm-Button nicht geklickt")
                return True

            # Formular absenden
            submitted = False
            for btn_name in ("Weiter", "Reservieren", "Buchen", "Bestätigen", "Confirm"):
                try:
                    btn = ctx.get_by_role("button", name=btn_name).first
                    if await btn.is_visible(timeout=2000):
                        await btn.click()
                        submitted = True
                        break
                except Exception:
                    pass
            if not submitted:
                await ctx.locator("button[type='submit']").first.click(timeout=5000)

            await page.wait_for_timeout(3000)
            await page.screenshot(path=f"screenshots/book_done_{event_date.strftime('%Y%m%d')}.png")
            logger.info(f"Buchung abgeschlossen: {event_date.strftime('%d.%m.%Y')} um {chosen}")
            return True
        except Exception as e:
            logger.error(f"Buchungsfehler ({detail_url}): {e}")
            return False
        finally:
            await browser.close()


async def cancel_booking(detail_url: str, event_date: datetime, event_title: str = "") -> bool:
    if settings.booking_dry_run:
        label = event_title or detail_url
        logger.info(f"[DRY-RUN] Würde stornieren: {label} am {event_date.strftime('%d.%m.%Y')}")
        return True
    # Resmio hat keine automatische Stornierung per Widget — manuelle Benachrichtigung
    logger.warning(
        f"Stornierung erforderlich: {event_title or detail_url} am {event_date.strftime('%d.%m.%Y')} "
        f"— bitte manuell bei Pension Schmidt stornieren."
    )
    return True
