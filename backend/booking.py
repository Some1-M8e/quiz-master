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
        day_selectors = [
            f"[data-date='{year}-{month:02d}-{day:02d}']",
            f"[data-day='{day}']",
            f".calendar-day[data-day='{day}']",
            f"button:has-text('{day}')",
            f"td[data-day='{day}']",
        ]

        for selector in day_selectors:
            try:
                day_btn = ctx.locator(selector).first
                if await day_btn.is_visible(timeout=1000):
                    await day_btn.click()
                    logger.info(f"Datum im Kalender gewählt: {date_de}")
                    await ctx.wait_for_timeout(1000)
                    return True
            except Exception:
                continue

        day_text_btn = ctx.get_by_text(str(day), exact=False).first
        if await day_text_btn.is_visible(timeout=2000):
            await day_text_btn.click()
            logger.info(f"Datum per Text gewählt: {date_de}")
            await ctx.wait_for_timeout(1000)
            return True

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

        # Modal ist offen - suche nach der Option mit der richtigen Anzahl
        # Resmio verwendet aria-label wie "11 Gäste" oder role="option"
        target_text = f"{count} Gäste"

        # Suche nach Option im Modal
        option_selector = f"div[role='option'][aria-label*='{count}'], .guestpicker-modal [role='option']:has-text('{count}')"
        try:
            option = ctx.locator(option_selector).first
            if await option.is_visible(timeout=2000):
                await option.click()
                logger.info(f"Gäste gesetzt auf {count}")
                await ctx.wait_for_timeout(1000)
                return True
        except Exception:
            pass

        # Fallback: Suche nach div mit aria-label containing the count
        for i in range(20):  # Prüfe bis 20 Optionen
            try:
                option = ctx.locator(f"div[role='option']").nth(i)
                text = await option.text_content() or ""
                aria_label = await option.get_attribute("aria-label") or ""
                if str(count) in aria_label or target_text in text:
                    await option.click()
                    logger.info(f"Gäste gesetzt auf {count} (Option {i})")
                    await ctx.wait_for_timeout(1000)
                    return True
            except Exception:
                continue

        # Nochmal Fallback: Suche nach div mit Text "X Gäste"
        try:
            option = ctx.get_by_text(target_text, exact=False).first
            if await option.is_visible(timeout=2000):
                await option.click()
                logger.info(f"Gäste gesetzt auf {count} (Text-Fallback)")
                await ctx.wait_for_timeout(1000)
                return True
        except Exception:
            pass

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
