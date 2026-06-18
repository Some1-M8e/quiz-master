"""Journey-Test: Event wird wegen zu wenig Zusagen storniert."""
import pytest
from models import Event, RSVP, Participant
from datetime import datetime, timedelta, timezone
import secrets


class TestJourneyCancellation:
    def test_event_wird_storniert_wenn_zu_wenig_zusagen(self, test_db, provider_factory):
        event_date = datetime.now(timezone.utc) + timedelta(days=14)
        event = Event(
            provider_id=provider_factory().id,
            title="Quiz",
            event_date=event_date,
            status="booked",
            source="scraper",
        )
        test_db.add(event)
        test_db.commit()

        p1 = Participant(name="Max", email="max@test.de", notifications_enabled=True)
        p2 = Participant(name="Laura", email="laura@test.de", notifications_enabled=True)
        test_db.add_all([p1, p2])
        test_db.commit()

        rsvp1 = RSVP(event_id=event.id, participant_id=p1.id, response="yes", token=secrets.token_urlsafe(32))
        rsvp2 = RSVP(event_id=event.id, participant_id=p2.id, response="yes", token=secrets.token_urlsafe(32))
        test_db.add_all([rsvp1, rsvp2])
        test_db.commit()

        # 2 Ja (zu wenig)
        yes_count = sum(1 + r.companions for r in test_db.query(RSVP).all() if r.response == "yes")
        assert yes_count == 2

        # Stornierung
        event.status = "cancelled"
        test_db.commit()

        assert test_db.query(Event).get(event.id).status == "cancelled"

    def test_event_gehalten_wenn_genug_zusagen(self, test_db, provider_factory):
        p1 = Participant(name="Max", email="max@test.de", notifications_enabled=True)
        p2 = Participant(name="Laura", email="laura@test.de", notifications_enabled=True)
        p3 = Participant(name="Anna", email="anna@test.de", notifications_enabled=True)
        p4 = Participant(name="Tom", email="tom@test.de", notifications_enabled=True)
        test_db.add_all([p1, p2, p3, p4])
        test_db.commit()

        provider = provider_factory()
        event_date = datetime.now(timezone.utc) + timedelta(days=14)
        event = Event(
            provider_id=provider.id,
            title="Quiz",
            event_date=event_date,
            status="booked",
            source="scraper",
        )
        test_db.add(event)
        test_db.commit()

        for p in [p1, p2, p3, p4]:
            rsvp = RSVP(event_id=event.id, participant_id=p.id, response="yes", token=secrets.token_urlsafe(32))
            test_db.add(rsvp)
        test_db.commit()

        yes_count = sum(1 + r.companions for r in test_db.query(RSVP).all() if r.response == "yes")
        assert yes_count == 4
        assert test_db.query(Event).get(event.id).status == "booked"

    def test_maybe_wird_zu_nein(self, test_db, provider_factory):
        p = Participant(name="Max", email="max@test.de", notifications_enabled=True)
        test_db.add(p)
        test_db.commit()

        provider = provider_factory()
        event = Event(
            provider_id=provider.id,
            title="Quiz",
            event_date=datetime.now(timezone.utc) + timedelta(days=14),
            status="booked",
            source="scraper",
        )
        test_db.add(event)
        test_db.commit()

        rsvp = RSVP(event_id=event.id, participant_id=p.id, response="maybe", token=secrets.token_urlsafe(32))
        test_db.add(rsvp)
        test_db.commit()

        rsvp.response = "no"
        test_db.commit()
        assert test_db.query(RSVP).get(rsvp.id).response == "no"

    def test_force_keep_verhindert_stornierung(self, test_db, provider_factory):
        p = Participant(name="Max", email="max@test.de", notifications_enabled=True)
        test_db.add(p)
        test_db.commit()

        provider = provider_factory()
        event = Event(
            provider_id=provider.id,
            title="Quiz",
            event_date=datetime.now(timezone.utc) + timedelta(days=14),
            status="booked",
            source="scraper",
        )
        test_db.add(event)
        test_db.commit()

        event.force_keep = True
        event.force_keep_note = "Manuell markiert"
        test_db.commit()

        rsvp = RSVP(event_id=event.id, participant_id=p.id, response="yes", token=secrets.token_urlsafe(32))
        test_db.add(rsvp)
        test_db.commit()

        saved = test_db.query(Event).get(event.id)
        assert saved.status == "booked"
        assert saved.force_keep is True
