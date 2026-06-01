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
            return frame

    logger.info("Resmio nicht als Popup/iframe gefunden — nutze Hauptseite")
    return page


async def _set_date(ctx, event_date: datetime) -> bool:
    date_iso = event_date.strftime("%Y-%m-%d")
    date_de = event_date.strftime("%d.%m.%Y")

    # HTML5 date input
    try:
        inp = ctx.locator("input[type='date']").first
        await inp.wait_for(state="visible", timeout=5000)
        await inp.fill(date_iso)
        await inp.press("Tab")
        return True
    except Exception:
        pass

    # Text-Input mit deutschem Format
    try:
        inp = ctx.locator("input[type='text']").first
        await inp.wait_for(state="visible", timeout=3000)
        await inp.triple_click()
        await inp.fill(date_de)
        await inp.press("Tab")
        return True
    except Exception:
        pass

    logger.warning("Datum-Feld nicht gefunden")
    return False


async def _set_guests(ctx, count: int = 4) -> bool:
    # Select-Element
    try:
        sel = ctx.locator("select").first
        await sel.wait_for(state="visible", timeout=5000)
        await sel.select_option(str(count))
        return True
    except Exception:
        pass

    # +/- Stepper
    try:
        plus = ctx.get_by_role("button", name="+").first
        current_el = ctx.locator("[data-guests],[data-count],[aria-valuetext]").first
        current = int(await current_el.text_content(timeout=3000) or "1")
        for _ in range(count - current):
            await plus.click()
        return True
    except Exception:
        pass

    logger.warning("Personenzahl-Feld nicht gefunden")
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
    if settings.booking_dry_run:
        logger.info(f"[DRY-RUN] Buchbarkeitsprüfung übersprungen für {detail_url}")
        return True

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
            await _set_guests(ctx, 4)
            await ctx.wait_for_timeout(2000)
            await page.screenshot(path=f"screenshots/check_3_{event_date.strftime('%Y%m%d')}.png")

            slots = await _available_slots(ctx)
            logger.info(f"Verfügbare Slots für {event_date.strftime('%d.%m.%Y')}: {slots or 'keine'}")
            return len(slots) > 0
        except Exception as e:
            logger.error(f"Buchbarkeitsprüfung fehlgeschlagen ({detail_url}): {e}")
            return False
        finally:
            await browser.close()


async def book_event(detail_url: str, event_date: datetime, event_title: str = "") -> bool:
    if settings.booking_dry_run:
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
            ctx = await _open_resmio(page, context)

            if not await _set_date(ctx, event_date):
                logger.error("Datum konnte nicht gesetzt werden")
                return False
            if not await _set_guests(ctx, 4):
                logger.error("Personenzahl konnte nicht gesetzt werden")
                return False

            await ctx.wait_for_timeout(2000)
            slots = await _available_slots(ctx)
            if not slots:
                logger.info(f"Keine freien Slots 19:00–19:30 für {event_date.strftime('%d.%m.%Y')}")
                return False

            # Späteste verfügbare Uhrzeit wählen
            chosen = slots[0]
            await ctx.get_by_text(chosen, exact=True).first.click(timeout=5000)
            await ctx.wait_for_timeout(2000)

            os.makedirs("screenshots", exist_ok=True)
            await page.screenshot(path=f"screenshots/book_slot_{event_date.strftime('%Y%m%d')}.png")

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

            await page.screenshot(path=f"screenshots/book_form_{event_date.strftime('%Y%m%d')}.png")

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
