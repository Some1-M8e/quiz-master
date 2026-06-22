import pytest
import sys
import os
import tempfile
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Wichtig: Damit main und models importiert werden können
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def test_db():
    """File-basierte SQLite für Tests (damit TestClient und Fixtures dieselbe DB nutzen)."""
    # Temporäre DB-Datei erstellen
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_url = f"sqlite:///{tmp.name}"

    from models import Provider, Event, Participant, RSVP, Setting
    from database import Base
    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = SessionLocal()
    yield db
    db.close()
    engine.dispose()
    # Cleanup
    try:
        os.unlink(tmp.name)
    except:
        pass


def _admin_token():
    from config import settings
    return settings.secret_key


@pytest.fixture
def client(test_db):
    """FastAPI TestClient mit derselben DB-Session.

    Der Scheduler wird im Test-Modus komplett deaktiviert, um
    Konflikte zwischen mehreren TestClient-Instanzen zu vermeiden.
    Email-Versand wird gemockt, damit kein echter SMTP-Server benötigt wird.
    """
    from main import app
    from database import get_db
    import scheduler as sched
    from email_service import (
        send_participant_welcome, send_invitation, send_rsvp_confirmation,
        send_booking_confirmation, send_cancellation, send_booking_warning,
        send_event_found_notification, send_participant_removed, send_reminder,
        send_maybe_reminder, send_weekly_reminder, send_maybe_timeout,
    )

    # Scheduler im Test-Modus komplett deaktivieren
    original_start = sched.start_scheduler
    sched.start_scheduler = lambda: None

    # Email-Versand für diesen Test vollständig mocken
    with patch("email_service._send") as mock_send:
        # Override so TestClient dieselbe DB nutzt
        app.dependency_overrides[get_db] = lambda: test_db

        with TestClient(app, headers={"Authorization": f"Bearer {_admin_token()}"}) as c:
            yield c
        app.dependency_overrides.clear()
    sched.start_scheduler = original_start


@pytest.fixture
def provider_factory(test_db):
    """Factory: erstelle einen Provider."""
    from models import Provider
    def _create(name="Pension Schmidt", url="https://www.pensionschmidt.se/programm"):
        p = Provider(name=name, url=url)
        test_db.add(p)
        test_db.commit()
        test_db.refresh(p)
        return p
    return _create


@pytest.fixture
def participant_factory(test_db):
    """Factory: erstelle einen Participant."""
    from models import Participant
    def _create(name="Max Mustermann", email="max@test.de"):
        p = Participant(name=name, email=email, notifications_enabled=True)
        test_db.add(p)
        test_db.commit()
        test_db.refresh(p)
        return p
    return _create


@pytest.fixture
def event_factory(test_db, provider_factory):
    """Factory: erstelle ein Event."""
    from datetime import datetime, timedelta
    from models import Event
    def _create(title="Quiz Quiz Bang Bang", event_date=None, status="pending", detail_url=None, provider=None):
        provider = provider or provider_factory()
        if event_date is None:
            event_date = datetime.now() + timedelta(days=14)
        e = Event(
            provider_id=provider.id,
            title=title,
            event_date=event_date,
            detail_url=detail_url or "https://example.com/event",
            description="Test Event",
            status=status,
            source="scraper",
        )
        test_db.add(e)
        test_db.commit()
        test_db.refresh(e)
        return e
    return _create


@pytest.fixture
def rsvp_factory(test_db, event_factory, participant_factory):
    """Factory: erstelle ein RSVP."""
    import secrets
    from models import RSVP
    def _create(event=None, participant=None, response="yes", companions=0, token=None):
        event = event or event_factory()
        participant = participant or participant_factory()
        r = RSVP(
            event_id=event.id,
            participant_id=participant.id,
            response=response,
            companions=companions,
            selected=True,
            token=token or secrets.token_urlsafe(32),
        )
        test_db.add(r)
        test_db.commit()
        test_db.refresh(r)
        return r
    return _create


@pytest.fixture
def mock_email_service():
    """Mock alle Email-Funktionen."""
    with patch("email_service.send_participant_welcome") as welcome, \
         patch("email_service.send_invitation") as invitation, \
         patch("email_service.send_rsvp_confirmation") as rsvp_conf, \
         patch("email_service.send_booking_confirmation") as booking, \
         patch("email_service.send_cancellation") as cancel, \
         patch("email_service.send_booking_warning") as warning, \
         patch("email_service.send_event_found_notification") as event_found, \
         patch("email_service.send_participant_removed") as removed, \
         patch("email_service.send_reminder") as reminder:
        yield {
            "welcome": welcome,
            "invitation": invitation,
            "rsvp": rsvp_conf,
            "booking": booking,
            "cancel": cancel,
            "warning": warning,
            "event_found": event_found,
            "removed": removed,
            "reminder": reminder,
        }


@pytest.fixture
def mock_httpx_get():
    """Mock httpx.get für Scraper-Tests."""
    with patch("httpx.get") as mock:
        yield mock


@pytest.fixture
def mock_playwright():
    """Mock playwright für Booking-Tests."""
    with patch("booking.asyncio.run") as mock:
        yield mock
