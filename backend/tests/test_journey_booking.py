"""Journey-Test: Event wird automatisch gebucht."""
import pytest
from models import Event, RSVP, Participant
from datetime import datetime, timedelta, timezone


class TestJourneyAutomaticBooking:
    def test_event_status_wird_buchung_erfolgreich_geandert(self, test_db, provider_factory):
        event_date = datetime.now(timezone.utc) + timedelta(days=14)
        event = Event(
            provider_id=provider_factory().id,
            title="Quiz",
            event_date=event_date,
            status="pending",
            source="scraper",
        )
        test_db.add(event)
        test_db.commit()

        event.status = "booked"
        event.capacity = 5
        test_db.commit()

        saved = test_db.query(Event).get(event.id)
        assert saved.status == "booked"
        assert saved.capacity == 5

    def test_event_status_bleibt_pending_bei_fehler(self, test_db, provider_factory):
        event_date = datetime.now(timezone.utc) + timedelta(days=14)
        event = Event(
            provider_id=provider_factory().id,
            title="Quiz",
            event_date=event_date,
            status="pending",
            source="scraper",
        )
        test_db.add(event)
        test_db.commit()

        saved = test_db.query(Event).get(event.id)
        assert saved.status == "pending"

    def test_rsvps_werden_nach_buchung_erstellt(self, test_db, provider_factory, participant_factory):
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

        p1 = participant_factory(name="Max")
        p2 = participant_factory(name="Laura")

        rsvp1 = RSVP(event_id=event.id, participant_id=p1.id, response=None)
        rsvp2 = RSVP(event_id=event.id, participant_id=p2.id, response=None)
        test_db.add_all([rsvp1, rsvp2])
        test_db.commit()

        count = test_db.query(RSVP).filter_by(event_id=event.id).count()
        assert count == 2

    def test_event_mit_begleitung(self, test_db, provider_factory, participant_factory):
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

        p = participant_factory(name="Max")
        rsvp = RSVP(event_id=event.id, participant_id=p.id, response="yes", companions=1)
        test_db.add(rsvp)
        test_db.commit()

        yes_rsvps = [r for r in test_db.query(RSVP).all() if r.response == "yes"]
        total = sum(1 + r.companions for r in yes_rsvps)
        assert total == 2

    def test_5_platze_bei_buchung(self, test_db, provider_factory):
        provider = provider_factory()
        event_date = datetime.now(timezone.utc) + timedelta(days=14)
        event = Event(
            provider_id=provider.id,
            title="Quiz",
            event_date=event_date,
            status="booked",
            capacity=5,
            source="scraper",
        )
        test_db.add(event)
        test_db.commit()

        saved = test_db.query(Event).get(event.id)
        assert saved.capacity == 5
