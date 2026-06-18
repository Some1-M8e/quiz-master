"""Tests für alle Email-Funktionen.

Mockt den internen _send, damit keine SMTP-Verbindung aufgebaut wird.
"""
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_send():
    with patch("email_service._send") as mock:
        yield mock


class TestSendParticipantWelcome:
    def test_wird_aufgerufen(self, mock_send):
        from email_service import send_participant_welcome
        send_participant_welcome("Max", "max@test.de")
        mock_send.assert_called_once()

    def test_betreff(self, mock_send):
        from email_service import send_participant_welcome
        send_participant_welcome("Max", "max@test.de")
        assert "Quiz-Master" in mock_send.call_args[0][1]

    def test_email_anrichtig(self, mock_send):
        from email_service import send_participant_welcome
        send_participant_welcome("Max", "max@test.de")
        assert mock_send.call_args[0][0] == "max@test.de"

    def test_body_enhaeltName(self, mock_send):
        from email_service import send_participant_welcome
        send_participant_welcome("Max", "max@test.de")
        assert "Hallo Max" in mock_send.call_args[0][2]


class TestSendParticipantRemoved:
    def test_wird_aufgerufen(self, mock_send):
        from email_service import send_participant_removed
        send_participant_removed("Max", "max@test.de")
        mock_send.assert_called_once()

    def test_betreff(self, mock_send):
        from email_service import send_participant_removed
        send_participant_removed("Max", "max@test.de")
        assert "entfernt" in mock_send.call_args[0][1]


class TestSendInvitation:
    def test_wird_aufgerufen(self, mock_send):
        from email_service import send_invitation
        send_invitation("Max", "max@test.de", "Quiz", "14.07.2026", "abc")
        mock_send.assert_called_once()

    def test_enhaelt_rsvp_links(self, mock_send):
        from email_service import send_invitation
        send_invitation("Max", "max@test.de", "Quiz", "14.07.2026", "xyz")
        assert "/rsvp/xyz/yes" in mock_send.call_args[0][2]

    def test_betreff_enhaeltTitel(self, mock_send):
        from email_service import send_invitation
        send_invitation("Max", "max@test.de", "Quiz Quiz Bang Bang", "14.07.2026", "x")
        assert "Quiz Quiz Bang Bang" in mock_send.call_args[0][1]


class TestSendRsvpConfirmation:
    def test_yes(self, mock_send):
        from email_service import send_rsvp_confirmation
        send_rsvp_confirmation("Max", "max@test.de", "Quiz", "14.07.2026", response="yes")
        assert "Zusage" in mock_send.call_args[0][1]

    def test_maybe(self, mock_send):
        from email_service import send_rsvp_confirmation
        send_rsvp_confirmation("Max", "max@test.de", "Quiz", "14.07.2026", response="maybe")
        assert "Vielleicht" in mock_send.call_args[0][1]


class TestSendBookingConfirmation:
    def test_wird_aufgerufen(self, mock_send):
        from email_service import send_booking_confirmation
        send_booking_confirmation("Max", "max@test.de", "Quiz", "14.07.2026")
        mock_send.assert_called_once()

    def test_betreff(self, mock_send):
        from email_service import send_booking_confirmation
        send_booking_confirmation("Max", "max@test.de", "Quiz", "14.07.2026")
        assert "gebucht" in mock_send.call_args[0][1]


class TestSendCancellation:
    def test_wird_aufgerufen(self, mock_send):
        from email_service import send_cancellation
        send_cancellation("Max", "max@test.de", "Quiz", "14.07.2026")
        mock_send.assert_called_once()

    def test_betreff(self, mock_send):
        from email_service import send_cancellation
        send_cancellation("Max", "max@test.de", "Quiz", "14.07.2026")
        assert "storniert" in mock_send.call_args[0][1]


class TestSendReminder:
    def test_wird_aufgerufen(self, mock_send):
        from email_service import send_reminder
        send_reminder("Max", "max@test.de", "Quiz", "14.07.2026")
        mock_send.assert_called_once()

    def test_enhaeltErinnerungstext(self, mock_send):
        from email_service import send_reminder
        send_reminder("Max", "max@test.de", "Quiz", "14.07.2026")
        body = mock_send.call_args[0][2]
        assert "Morgen" in body


class TestSendMaybeReminder:
    def test_wird_aufgerufen(self, mock_send):
        from email_service import send_maybe_reminder
        send_maybe_reminder("Max", "max@test.de", "Quiz", "14.07.2026", "t123")
        mock_send.assert_called_once()

    def test_enhaeltFrist(self, mock_send):
        from email_service import send_maybe_reminder
        send_maybe_reminder("Max", "max@test.de", "Quiz", "14.07.2026", "t123")
        assert "48 Stunden" in mock_send.call_args[0][2]


class TestSendEventFoundNotification:
    def test_wird_aufgerufen(self, mock_send):
        from email_service import send_event_found_notification
        send_event_found_notification("Max", "max@test.de", "Pensionär?", "14.07.2026", "", "https://example.com")
        mock_send.assert_called_once()

    def test_enhaeltBuchungslink(self, mock_send):
        from email_service import send_event_found_notification
        send_event_found_notification("Max", "max@test.de", "Pensionär?", "14.07.2026", "", "https://example.com")
        body = mock_send.call_args[0][2]
        assert "Zum Buchungstool" in body


class TestQuizCategory:
    def test_verquizmeinnicht(self):
        from email_service import _quiz_category
        assert _quiz_category("VerQUIZmeinnicht") == "Allgemeinwissensquiz"

    def test_quiz_quiz_bang_bang(self):
        from email_service import _quiz_category
        assert _quiz_category("Quiz Quiz Bang Bang") == "Filme- und Serien-Quiz"

    def test_unbekannt(self):
        from email_service import _quiz_category
        assert _quiz_category("Blabla") is None
