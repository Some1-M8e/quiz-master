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
    """Stellt das Datum über den Resmio Kalender-Wähler ein."""
    date_de = event_date.strftime("%d.%m.%Y")
    day = event_date.day
    month = event_date.month
    year = event_date.year

    # Wartezeit nach Resmio-Öffnung
    await ctx.wait_for_timeout(3000)

    # 1. Auf den Datum-Button klicken (Resmio verwendet ".date-picker" Button mit Text "Heute")
    try:
        date_picker = ctx.locator(".date-picker").first
        if not await date_picker.is_visible(timeout=2000):
            date_picker = ctx.get_by_text("Heute", exact=False).first
        if not await date_picker.is_visible(timeout=2000):
            date_picker = ctx.get_by_text("Datum", exact=False).first
        if not await date_picker.is_visible(timeout=2000):
            raise Exception("Kein Date-Picker Button gefunden")

        await date_picker.click()
        await ctx.wait_for_timeout(2000)
        logger.info("Datum-Button (Kalender) geöffnet")
    except Exception as e:
        logger.warning(f"Date-Picker nicht gefunden: {e}")
        return False

    # 3. Im Kalender das richtige Datum klicken
    try:
        # Resmio verwendet .datepicker-cell mit Text-Inhalt (z.B. "25")
        # Nicht-wählbare Tage haben class "is-unselectable"
        cells = await ctx.locator(".datepicker-cell").all()
        for cell in cells:
            text = await cell.text_content() or ""
            if text.strip() == str(day):
                cls = await cell.get_attribute("class") or ""
                if "is-unselectable" not in cls:
                    await cell.click()
                    logger.info(f"Datum im Kalender gewählt: {date_de}")
                    await ctx.wait_for_timeout(1000)
                    return True

        logger.error(f"Konnte Datum {date_de} nicht setzen")
        return False

    except Exception as e:
        logger.warning(f"Kalender-Datum nicht gefunden: {e}")

    logger.error(f"Konnte Datum {date_de} nicht setzen")
    return False


async def _set_guests(ctx, count: int = 4) -> bool:
    """Stellt die Anzahl der Gäste über den Resmio guest-picker Modal ein."""
    try:
        # Resmio verwendet einen Button ".guest-picker" mit Text wie "2 Gäste"
        guest_picker = ctx.locator(".guest-picker").first
        if not await guest_picker.is_visible(timeout=2000):
            guest_picker = ctx.get_by_text("Gäste", exact=False).first
        if not await guest_picker.is_visible(timeout=2000):
            raise Exception("Kein Guest-Picker Button gefunden")

        await guest_picker.click()
        await ctx.wait_for_timeout(1500)

        # Resmio zeigt Gäste als einfachen Text an (z.B. "4 Gäste", "4 Gaste", "4 Guests")
        # Suche nach mehreren Varianten um Encoding-Probleme zu vermeiden
        variants = [
            f"{count} Gäste",   # Mit Umlaut
            f"{count} Gaste",   # Ohne Umlaut
            f"{count} Guests",  # Englisch
            f"{count} Gast",    # Singular
        ]

        for text in variants:
            option = ctx.get_by_text(text, exact=False).first
            if await option.is_visible(timeout=500):
                await option.click()
                logger.info(f"Gäste gesetzt auf {count}")
                await ctx.wait_for_timeout(1000)
                return True

        logger.warning(f"Keine Option für {count} Gäste gefunden (versucht: {variants})")
        return False

    except Exception as e:
        logger.warning(f"Guest-Picker fehlgeschlagen: {e}")
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

            # Slot-Text lesen (darunter steht ggf. "not available")
            slot_text = await slot.text_content() or ""
            # Cursor prüfen (not-allowed = nicht selektierbar)
            cursor = await slot.evaluate("""el => {
                const computed = window.getComputedStyle(el.parentElement);
                return computed.cursor;
            }""")

            # Nicht buchbar = "not available" Text ODER nicht selektierbar (cursor=not-allowed)
            has_not_available = "not available" in slot_text.lower()
            is_not_selectable = cursor == "not-allowed"

            if has_not_available or is_not_selectable:
                logger.debug(f"Slot {t}: nicht buchbar (not available={has_not_available}, cursor={cursor})")
                continue

            # Slot ist verfügbar
            available.append(t)
            logger.debug(f"Slot {t}: buchbar")
        except Exception as e:
            logger.debug(f"Slot {t}: Fehler bei Prüfung - {e}")
            pass

    logger.info(f"Verfügbare Slots: {available}")
    if not available:
        logger.info("Keine der Ziel-Slots (19:00, 19:15, 19:30) sind buchbar")
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
            slot_btn = ctx.get_by_text(chosen, exact=True).first

            # Prüfen ob der Slot wirklich klickbar ist (nicht disabled / not available)
            is_disabled = await slot_btn.get_attribute("disabled")
            aria_disabled = await slot_btn.get_attribute("aria-disabled")
            slot_class = await slot_btn.get_attribute("class") or ""

            if is_disabled or aria_disabled == "true" or "not-available" in slot_class.lower():
                logger.error(f"Slot {chosen} ist nicht verfügbar (disabled/not-available) - Event ist ausgebucht!")
                return False

            # Prüfen ob "not available" Text in der Nähe steht
            try:
                slot_text = await slot_btn.text_content(timeout=1000) or ""
                if "not available" in slot_text.lower() or "ausgebucht" in slot_text.lower():
                    logger.error(f"Slot {chosen} zeigt 'not available' - Event ist ausgebucht!")
                    return False
            except Exception:
                pass

            await slot_btn.click(timeout=5000)
            await page.wait_for_timeout(3000)
            await page.screenshot(path="screenshots/test_05_uhrzeit_gewaehlt.png")
            logger.info(f"Schritt 5: Uhrzeit gewählt: {chosen}")

            # Warten bis "Weiter" enabled ist (bis zu 10 Sekunden)
            logger.info("Warte auf Weiter-Button...")
            for i in range(10):
                try:
                    weiter_btn = ctx.get_by_text("Weiter", exact=False).first
                    if await weiter_btn.is_enabled(timeout=500):
                        logger.info(f"Weiter-Button ist jetzt enabled nach {i+1} Sekunden")
                        break
                except Exception:
                    pass
                await page.wait_for_timeout(1000)
            else:
                logger.error("Weiter-Button wurde nach 10 Sekunden immer noch nicht enabled - Buchung abgebrochen")
                return False

            if stop_before_confirm:
                logger.info("STOPP vor Weiter-Button (Testmodus)")
                await page.screenshot(path="screenshots/test_06_vor_weiter_stopp.png")
                return True

            # Schritt 6: "Weiter" klicken (geht zur Kontaktseite)
            logger.info("Schritt 6: Weiter-Button klicken...")
            weiter_btn = ctx.get_by_text("Weiter", exact=False).first
            if not await weiter_btn.is_visible(timeout=3000):
                logger.error("Weiter-Button nicht gefunden")
                return False
            await weiter_btn.click()
            await page.wait_for_timeout(3000)
            logger.info("Weiter geklickt - gehe zur Kontaktseite")

            await page.screenshot(path="screenshots/test_07_kontaktseite.png")

            # Schritt 7: Kontaktdaten auf der Kontaktseite ausfüllen
            logger.info("Schritt 7: Kontaktdaten ausfüllen...")
            name_filled = False
            for selector in ("input[name='name']", "input[placeholder*='Name']", "input[placeholder*='name']", "input#name"):
                try:
                    inp = ctx.locator(selector).first
                    if await inp.is_visible(timeout=2000):
                        await inp.fill(settings.organizer_name)
                        name_filled = True
                        logger.info(f"Name ausgefüllt: {settings.organizer_name}")
                        break
                except Exception:
                    continue

            email_filled = False
            for selector in ("input[type='email']", "input[name='email']", "input#email"):
                try:
                    inp = ctx.locator(selector).first
                    if await inp.is_visible(timeout=2000):
                        await inp.fill(settings.organizer_email)
                        email_filled = True
                        logger.info(f"Email ausgefüllt: {settings.organizer_email}")
                        break
                except Exception:
                    continue

            if settings.organizer_phone:
                for selector in ("input[type='tel']", "input[name='phone']", "input#phone"):
                    try:
                        inp = ctx.locator(selector).first
                        if await inp.is_visible(timeout=2000):
                            await inp.fill(settings.organizer_phone)
                            logger.info(f"Phone ausgefüllt: {settings.organizer_phone}")
                            break
                    except Exception:
                        continue

            await page.screenshot(path="screenshots/test_08_kontaktdaten_ausgefuellt.png")
            logger.info(f"Schritt 7: Kontaktdaten ausgefüllt (Name={name_filled}, Email={email_filled})")

            # Schritt 8: Nachricht eintragen
            logger.info("Schritt 8: Nachricht eintragen...")
            for selector in ("textarea", "input[name='message']", "input[name='note']", "[placeholder*='Nachricht']", "[placeholder*='message']"):
                try:
                    msg_inp = ctx.locator(selector).first
                    if await msg_inp.is_visible(timeout=2000):
                        await msg_inp.fill("Diese Buchung wurde von einer KI für mich durchgeführt. Bei Problemen bitte anrufen!!")
                        logger.info("Nachricht ausgefüllt")
                        break
                except Exception:
                    continue

            await page.screenshot(path="screenshots/test_09_nachricht_eingetragen.png")
            logger.info("Schritt 8: Nachricht eingetragen")

            # Schritt 9: Exakt nach "Confirm" suchen
            logger.info("Schritt 9: Nach 'Confirm'-Button suchen...")
            confirm_btn = ctx.get_by_text("Confirm", exact=True).first
            if not await confirm_btn.is_visible(timeout=5000):
                logger.error("Confirm-Button NICHT gefunden - Buchung wurde NICHT abgeschlossen!")
                return False

            await confirm_btn.click()
            logger.info("Confirm-Button geklickt!")

            await page.wait_for_timeout(5000)
            await page.screenshot(path=f"screenshots/book_done_{event_date.strftime('%Y%m%d')}.png")
            logger.info(f"Buchung erfolgreich: {event_date.strftime('%d.%m.%Y')} um {chosen}")
            return True
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
