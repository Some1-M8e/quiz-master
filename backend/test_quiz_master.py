"""
Testfälle für Quiz-Master
==========================
Prüft die wichtigsten Verhaltensregeln:
  1. Quiz-Typ-Erkennung (nur VerQUIZmeinnicht und Quiz Quiz Bang Bang)
  2. Inhalte in E-Mails (Titel, Beschreibung, Kategorie-Badge)
  3. Scraper-Filterung (was landet in der DB, was wird ignoriert)
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

from email_service import _quiz_category, _event_info_block


# ══════════════════════════════════════════════════════
# 1.  Quiz-Typ-Erkennung
# ══════════════════════════════════════════════════════

class TestQuizTypErkennung:

    def test_verquizmeinnicht_ist_allgemeinwissensquiz(self):
        assert _quiz_category("VerQUIZmeinnicht #15") == "Allgemeinwissensquiz"

    def test_quiz_quiz_bang_bang_ist_film_und_serien_quiz(self):
        assert _quiz_category("Quiz Quiz Bang Bang – Staffel 3") == "Filme- und Serien-Quiz"

    def test_unbekanntes_event_hat_keine_kategorie(self):
        """Konzerte, Lesungen oder andere Events dürfen nicht erkannt werden."""
        assert _quiz_category("Konzertabend im Hinterhof") is None
        assert _quiz_category("Poetry Slam") is None
        assert _quiz_category("Pub Night") is None

    def test_erkennung_ignoriert_gross_und_kleinschreibung(self):
        assert _quiz_category("verquizmeinnicht spezial") == "Allgemeinwissensquiz"
        assert _quiz_category("QUIZ QUIZ BANG BANG") == "Filme- und Serien-Quiz"


# ══════════════════════════════════════════════════════
# 2.  E-Mail-Inhalte
# ══════════════════════════════════════════════════════

class TestEmailInhalte:

    def test_einladung_enthält_kategorie_badge_verquizmeinnicht(self):
        html = _event_info_block("VerQUIZmeinnicht #15", "15.06.2026", "")
        assert "Allgemeinwissensquiz" in html

    def test_einladung_enthält_kategorie_badge_filmquiz(self):
        html = _event_info_block("Quiz Quiz Bang Bang", "15.06.2026", "")
        assert "Filme- und Serien-Quiz" in html

    def test_einladung_enthält_beschreibung(self):
        html = _event_info_block("VerQUIZmeinnicht #15", "15.06.2026", "Wer weiß am meisten?")
        assert "Wer weiß am meisten?" in html

    def test_einladung_enthält_immer_titel_und_datum(self):
        html = _event_info_block("Quiz Quiz Bang Bang", "20.07.2026", "")
        assert "Quiz Quiz Bang Bang" in html
        assert "20.07.2026" in html

    def test_kein_kategorie_badge_bei_unbekanntem_event(self):
        """Falls doch mal ein unbekanntes Event in die Mail käme, darf kein falscher Badge erscheinen."""
        html = _event_info_block("Sonstige Veranstaltung", "01.06.2026", "")
        assert "Allgemeinwissensquiz" not in html
        assert "Filme- und Serien-Quiz" not in html

    def test_leere_beschreibung_erzeugt_keinen_leeren_block(self):
        html = _event_info_block("VerQUIZmeinnicht #15", "15.06.2026", "")
        # Kein leerer <p>-Tag mit nur Leerzeichen
        assert "<p></p>" not in html


# ══════════════════════════════════════════════════════
# Hilfsfunktionen für Scraper-Tests
# ══════════════════════════════════════════════════════

def _html_event(title: str, date_str: str, status: str = "", has_button: bool = True, has_title_link: bool = True) -> str:
    """Baut ein Squarespace-ähnliches Event-HTML-Element."""
    btn = '<a href="/events/test-event" class="eventlist-button">Veranstaltung ansehen</a>' if has_button else ""
    status_tag = f'<div class="eventlist-datetag-status">{status}</div>' if status else ""
    title_content = f'<a href="/events/test-event">{title}</a>' if has_title_link else title
    return f"""
    <article class="eventlist-event eventlist-event--upcoming">
        <time class="event-date" datetime="{date_str}">{date_str}</time>
        <h1 class="eventlist-title">
            {title_content}
        </h1>
        {status_tag}
        <div class="eventlist-description">Testbeschreibung</div>
        {btn}
    </article>
    """


def _run_scrape(html: str, bookable: bool = True) -> list[dict]:
    """Führt scrape_provider mit gefälschtem HTTP-Response und gemockter Buchbarkeitsprüfung aus."""
    from scraper import scrape_provider

    provider = MagicMock()
    provider.id = 1
    provider.url = "https://www.pensionschmidt.se/programm"

    db = MagicMock()
    db.query.return_value.filter_by.return_value.first.return_value = None  # Event noch nicht in DB

    mock_response = MagicMock()
    mock_response.text = html
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response), \
         patch("booking.check_bookable", new_callable=AsyncMock) as mock_check:
        mock_check.return_value = bookable
        return scrape_provider(provider, db)


# ══════════════════════════════════════════════════════
# 3.  Scraper-Filterung
# ══════════════════════════════════════════════════════

class TestScraperFilterung:

    def _in_10_tagen(self) -> str:
        return (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")

    def _in_45_tagen(self) -> str:
        return (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d")

    # — Positiv: diese Events sollen gefunden werden —

    def test_verquizmeinnicht_wird_als_neuer_termin_erkannt(self):
        html = _html_event("VerQUIZmeinnicht #15", self._in_10_tagen())
        events = _run_scrape(html)
        assert len(events) == 1
        assert events[0]["title"] == "VerQUIZmeinnicht #15"

    def test_quiz_quiz_bang_bang_wird_als_neuer_termin_erkannt(self):
        html = _html_event("Quiz Quiz Bang Bang – Staffel 3", self._in_10_tagen())
        events = _run_scrape(html)
        assert len(events) == 1

    # — Negativ: diese Events sollen ignoriert werden —

    def test_konzert_oder_andere_events_werden_ignoriert(self):
        """Kein Quiz-Typ → wird nicht in die DB eingetragen."""
        html = _html_event("Konzertabend", self._in_10_tagen())
        events = _run_scrape(html)
        assert len(events) == 0

    def test_ausverkauftes_quiz_wird_ignoriert(self):
        html = _html_event("VerQUIZmeinnicht #15", self._in_10_tagen(), status="Ausverkauft")
        events = _run_scrape(html)
        assert len(events) == 0

    def test_abgesagtes_quiz_wird_ignoriert(self):
        html = _html_event("Quiz Quiz Bang Bang", self._in_10_tagen(), status="Abgesagt")
        events = _run_scrape(html)
        assert len(events) == 0

    def test_quiz_mehr_als_30_tage_in_zukunft_wird_ignoriert(self):
        """Pension Schmidt öffnet Reservierungen erst einen Monat vorher."""
        html = _html_event("VerQUIZmeinnicht #15", self._in_45_tagen())
        events = _run_scrape(html)
        assert len(events) == 0

    def test_nicht_buchbares_quiz_wird_ignoriert(self):
        """Kein freier Slot 19:00–19:30 → kein Eintrag in die DB."""
        html = _html_event("VerQUIZmeinnicht #15", self._in_10_tagen())
        events = _run_scrape(html, bookable=False)
        assert len(events) == 0

    def test_quiz_ohne_detail_link_wird_ignoriert(self):
        """Ohne Link können wir nicht buchen, also überspringen."""
        html = _html_event("VerQUIZmeinnicht #15", self._in_10_tagen(), has_button=False, has_title_link=False)
        events = _run_scrape(html)
        assert len(events) == 0

    # — Datenqualität —

    def test_detail_url_wird_korrekt_zusammengesetzt(self):
        html = _html_event("VerQUIZmeinnicht #15", self._in_10_tagen())
        events = _run_scrape(html)
        assert events[0]["detail_url"] == "https://www.pensionschmidt.se/events/test-event"

    def test_beschreibung_wird_aus_html_extrahiert(self):
        html = _html_event("VerQUIZmeinnicht #15", self._in_10_tagen())
        events = _run_scrape(html)
        assert events[0]["description"] == "Testbeschreibung"
