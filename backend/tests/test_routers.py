"""Integration-Tests für Router-Endpoints."""
import pytest
from unittest.mock import patch


class TestProviders:
    def test_get_providers_empty(self, client):
        resp = client.get("/providers")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_provider(self, client):
        resp = client.post("/providers", json={"name": "Neuer Anbieter", "url": "https://test.de"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Neuer Anbieter"

    def test_get_after_create(self, client):
        client.post("/providers", json={"name": "Test Provider", "url": "https://test.de"})
        resp = client.get("/providers")
        assert len(resp.json()) >= 1


class TestParticipants:
    def test_get_participants_empty(self, client):
        resp = client.get("/participants")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @patch("main.send_participant_welcome")
    def test_create_participant(self, mock, client):
        resp = client.post("/participants", json={"name": "Max", "email": "max@test.de"})
        assert resp.status_code == 201
        assert resp.json()["name"] == "Max"
        assert mock.called

    def test_duplicate_email_rejected(self, client):
        with patch("main.send_participant_welcome"):
            client.post("/participants", json={"name": "Max", "email": "max@test.de"})
        resp = client.post("/participants", json={"name": "Max2", "email": "max@test.de"})
        assert resp.status_code == 409

    def test_delete_participant(self, client):
        with patch("main.send_participant_removed"):
            resp = client.post("/participants", json={"name": "Max", "email": "max@test.de"})
            pid = resp.json()["id"]
        resp = client.delete(f"/participants/{pid}")
        assert resp.status_code == 204


class TestEvents:
    def test_get_events_empty(self, client):
        resp = client.get("/events")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestRsvpViaLink:
    def test_invalid_token(self, client):
        resp = client.get("/rsvp/doesnotexist/yes")
        assert resp.status_code == 404


class TestAuth:
    def test_invite_link(self, client):
        resp = client.get("/admin/invite")
        assert resp.status_code == 200
        assert "token" in resp.json()

    def test_validate_invite_valid(self, client):
        resp = client.get("/invite/quizmaster")
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    @patch("main.send_participant_welcome")
    def test_register_via_invite(self, mock, client):
        resp = client.post("/invite/quizmaster", json={"name": "Max", "email": "max@test.de"})
        assert resp.status_code == 201
        assert mock.called

    def test_register_duplicate(self, client):
        with patch("main.send_participant_welcome"):
            client.post("/invite/quizmaster", json={"name": "Max", "email": "max@test.de"})
        resp = client.post("/invite/quizmaster", json={"name": "Max2", "email": "max@test.de"})
        assert resp.status_code == 409


class TestAdmin:
    def test_run_scraper(self, client):
        resp = client.post("/admin/scraper/run")
        assert resp.status_code == 200
        assert resp.json()["message"] == "Scraper gestartet"
