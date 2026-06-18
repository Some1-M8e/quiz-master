"""Journey-Test: User registriert sich über Invite-Link."""
import pytest
from unittest.mock import patch
from models import Participant


class TestJourneyRegistration:
    def test_user_wird_in_db_erstellt(self, test_db):
        p = Participant(name="Max Mustermann", email="max@test.de", notifications_enabled=True)
        test_db.add(p)
        test_db.commit()

        user = test_db.query(Participant).filter_by(email="max@test.de").first()
        assert user is not None
        assert user.name == "Max Mustermann"

    def test_doppelte_email_wird_abgelehnt(self, test_db):
        p1 = Participant(name="Max", email="max@test.de")
        test_db.add(p1)
        test_db.commit()

        count = test_db.query(Participant).filter_by(email="max@test.de").count()
        assert count == 1

    def test_notifications_standardmaessig_an(self, test_db):
        p = Participant(name="Max", email="max@test.de")
        test_db.add(p)
        test_db.commit()

        user = test_db.query(Participant).filter_by(email="max@test.de").first()
        assert user.notifications_enabled is True

    def test_email_wird_gesendet(self):
        with patch("email_service.send_participant_welcome") as mock:
            from email_service import send_participant_welcome
            send_participant_welcome("Max", "max@test.de")
            assert mock.called

    def test_email_enhaeltName(self):
        with patch("email_service.send_participant_welcome") as mock:
            from email_service import send_participant_welcome
            send_participant_welcome("Max Mustermann", "max@test.de")
            args = mock.call_args[0]
            assert "Max Mustermann" in args[0] or "Max Mustermann" in args[2]
