"""Tests für backend/scraper.py."""
import pytest


class TestNormalizeTitle:
    def test_normal(self):
        from scraper import _normalize_title
        assert _normalize_title("Quiz Quiz Bang Bang") == "quiz quiz bang bang"

    def test_umlaut(self):
        from scraper import _normalize_title
        assert _normalize_title("Wer wird Pensionär?") == "wer wird pensionar?"

    def test_uppercase(self):
        from scraper import _normalize_title
        assert _normalize_title("QUIZ QUIZ BANG BANG") == "quiz quiz bang bang"

    def test_whitespace(self):
        from scraper import _normalize_title
        assert _normalize_title("  VerQUIZmeinnicht  ") == "verquizmeinnicht"


class TestIsExcludedFromBooking:
    def test_pensionar_excluded(self):
        from scraper import _is_excluded_from_booking
        assert _is_excluded_from_booking("Wer wird Pensionär?") is True

    def test_quiz_nicht_excluded(self):
        from scraper import _is_excluded_from_booking
        assert _is_excluded_from_booking("Quiz Quiz Bang Bang") is False


class TestExtractDetailUrl:
    def test_from_button(self):
        """Event-DIV mit eventlist-button extrahiert URL."""
        from scraper import _extract_detail_url
        from bs4 import BeautifulSoup
        html = '<div class="eventlist-event"><div class="eventlist-button"><a href="https://example.com/event">Link</a></div></div>'
        el = BeautifulSoup(html, "html.parser").find("div", class_="eventlist-event")
        result = _extract_detail_url(el, "https://example.com")
        assert result == "https://example.com/event"

    def test_from_title_link(self):
        """Event-DIV mit eventlist-title (Fallback) extrahiert URL."""
        from scraper import _extract_detail_url
        from bs4 import BeautifulSoup
        html = '<div class="eventlist-event"><span class="eventlist-title"><a href="/event">Titel</a></span></div>'
        el = BeautifulSoup(html, "html.parser").find("div", class_="eventlist-event")
        result = _extract_detail_url(el, "https://example.com/page")
        assert result == "https://example.com/event"

    def test_no_href(self):
        from scraper import _extract_detail_url
        from bs4 import BeautifulSoup
        html = '<div class="eventlist-event"><p>Kein Link</p></div>'
        el = BeautifulSoup(html, "html.parser").find("div", class_="eventlist-event")
        assert _extract_detail_url(el, "https://example.com") is None
