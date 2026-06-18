"""Journey-Test: User klickt auf Event, antwortet RSVP."""
import pytest
from models import RSVP, Event, Participant
from datetime import datetime, timedelta, timezone
import secrets


class TestJourneyRsvp:
    def test_user_kann_event_sehen(self, test_db, event_factory):
        event = event_factory(title="Quiz Quiz Bang Bang")
        events = test_db.query(Event).filter_by(title="Quiz Quiz Bang Bang").all()
        assert len(events) >= 1

    def test_user_kann_rsvp_geben_yes(self, test_db, event_factory, participant_factory):
        event = event_factory()
        participant = participant_factory()

        rsvp = RSVP(
            event_id=event.id,
            participant_id=participant.id,
            response=None,
            token=secrets.token_urlsafe(32),
        )
        test_db.add(rsvp)
        test_db.commit()
        rsvp_id = rsvp.id

        rsvp.response = "yes"
        rsvp.companions = 0
        test_db.commit()

        updated = test_db.query(RSVP).get(rsvp_id)
        assert updated.response == "yes"

    def test_user_kann_rsvp_geben_maybe(self, test_db, event_factory, participant_factory):
        event = event_factory()
        participant = participant_factory()

        rsvp = RSVP(
            event_id=event.id,
            participant_id=participant.id,
            response=None,
            token=secrets.token_urlsafe(32),
        )
        test_db.add(rsvp)
        test_db.commit()
        rsvp_id = rsvp.id

        rsvp.response = "maybe"
        test_db.commit()

        updated = test_db.query(RSVP).get(rsvp_id)
        assert updated.response == "maybe"

    def test_user_kann_rsvp_geben_no(self, test_db, event_factory, participant_factory):
        event = event_factory()
        participant = participant_factory()

        rsvp = RSVP(
            event_id=event.id,
            participant_id=participant.id,
            response=None,
            token=secrets.token_urlsafe(32),
        )
        test_db.add(rsvp)
        test_db.commit()
        rsvp_id = rsvp.id

        rsvp.response = "no"
        test_db.commit()

        updated = test_db.query(RSVP).get(rsvp_id)
        assert updated.response == "no"

    def test_user_mit_begleitung(self, test_db, event_factory, participant_factory):
        event = event_factory()
        participant = participant_factory()

        rsvp = RSVP(
            event_id=event.id,
            participant_id=participant.id,
            response=None,
            token=secrets.token_urlsafe(32),
        )
        test_db.add(rsvp)
        test_db.commit()
        rsvp_id = rsvp.id

        rsvp.response = "yes"
        rsvp.companions = 1
        test_db.commit()

        updated = test_db.query(RSVP).get(rsvp_id)
        assert updated.companions == 1

    def test_yes_zaehlt_fuer_total_attendees(self, test_db, event_factory, participant_factory):
        event = event_factory()
        p1 = participant_factory(name="Max")
        p2 = participant_factory(name="Laura")

        rsvp1 = RSVP(event_id=event.id, participant_id=p1.id, response="yes", companions=1)
        rsvp2 = RSVP(event_id=event.id, participant_id=p2.id, response="yes", companions=0)
        test_db.add_all([rsvp1, rsvp2])
        test_db.commit()

        yes_rsvps = [r for r in test_db.query(RSVP).all() if r.response == "yes"]
        total = sum(1 + r.companions for r in yes_rsvps)
        assert total == 3
