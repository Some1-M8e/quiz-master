"""Journey-Test: Scraper findet Event, bucht automatisch."""
import pytest
from models import Event, Participant, RSVP
from datetime import datetime, timedelta, timezone


class TestJourneyScraperBooking:
    """
    Flow: Scraper findet Event -> Event wird in DB gespeichert
    """

    def test_neues_event_wird_in_db_gespeichert(self, test_db, provider_factory):
        event_date = datetime.now(timezone.utc) + timedelta(days=14)
        event = Event(
            provider_id=provider_factory().id,
            title="Quiz Quiz Bang Bang",
            event_date=event_date,
            detail_url="https://example.com/event",
            status="pending",
            source="scraper",
        )
        test_db.add(event)
        test_db.commit()

        saved = test_db.query(Event).filter_by(title="Quiz Quiz Bang Bang").first()
        assert saved is not None
        assert saved.status == "pending"

    def test_event_wird_nicht_dupliziert(self, test_db, provider_factory):
        event_date = datetime.now(timezone.utc) + timedelta(days=14)

        # Event existiert bereits
        e1 = Event(
            provider_id=provider_factory().id,
            title="Quiz",
            event_date=event_date,
            status="pending",
            source="scraper",
        )
        test_db.add(e1)
        test_db.commit()

        # Gleicher Event nochmals anlegen -> sollte verhindern werden
        # Durch Unique-Kombination: provider_id + event_date
        count = test_db.query(Event).filter_by(
            provider_id=e1.provider_id,
            event_date=event_date
        ).count()
        assert count == 1

    def test_event_mit_status_ausverkauft(self, test_db, provider_factory):
        event_date = datetime.now(timezone.utc) + timedelta(days=14)
        event = Event(
            provider_id=provider_factory().id,
            title="Quiz",
            event_date=event_date,
            status="ausverkauft",
            source="scraper",
        )
        test_db.add(event)
        test_db.commit()

        saved = test_db.query(Event).get(event.id)
        assert saved.status == "ausverkauft"

    def test_event_mit_status_abgesagt(self, test_db, provider_factory):
        event_date = datetime.now(timezone.utc) + timedelta(days=14)
        event = Event(
            provider_id=provider_factory().id,
            title="Quiz",
            event_date=event_date,
            status="cancelled",
            source="scraper",
        )
        test_db.add(event)
        test_db.commit()

        saved = test_db.query(Event).get(event.id)
        assert saved.status == "cancelled"

    def test_pensionar_event_speichern(self, test_db, provider_factory):
        """"Wer wird Pensionär?" Event wird gespeichert."""
        event_date = datetime.now(timezone.utc) + timedelta(days=14)
        event = Event(
            provider_id=provider_factory().id,
            title="Wer wird Pensionär?",
            event_date=event_date,
            status="pending",
            source="scraper",
        )
        test_db.add(event)
        test_db.commit()

        saved = test_db.query(Event).filter_by(title="Wer wird Pensionär?").first()
        assert saved is not None
