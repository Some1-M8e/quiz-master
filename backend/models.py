import secrets
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class Provider(Base):
    __tablename__ = "providers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    url: Mapped[str] = mapped_column(String(500), unique=True)
    events: Mapped[list["Event"]] = relationship(back_populates="provider")

class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(200))
    event_date: Mapped[datetime] = mapped_column(DateTime)
    detail_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    status: Mapped[str] = mapped_column(SAEnum("pending", "booked", "cancelled", "ausverkauft", "teilweise_ausverkauft", name="event_status"), default="pending")
    capacity: Mapped[int] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(SAEnum("scraper", "manual", name="event_source"), default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    force_keep: Mapped[bool] = mapped_column(default=False)  # Manuell zum Behalten markiert
    force_keep_note: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Notiz zum Grund
    provider: Mapped["Provider"] = relationship(back_populates="events")
    rsvps: Mapped[list["RSVP"]] = relationship(back_populates="event", cascade="all, delete-orphan")

class Participant(Base):
    __tablename__ = "participants"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)  # Optional, keine Unique-Beschränkung
    notifications_enabled: Mapped[bool] = mapped_column(default=True)  # Benachrichtigungen abbestellbar
    rsvps: Mapped[list["RSVP"]] = relationship(back_populates="participant")


class RSVP(Base):
    __tablename__ = "rsvps"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id"))
    response: Mapped[str | None] = mapped_column(SAEnum("yes", "no", "maybe", name="rsvp_response", create_constraint=False), nullable=True)
    companions: Mapped[int] = mapped_column(Integer, default=0)  # Max 1 Begleitung (wird im Frontend erzwungen)
    selected: Mapped[bool] = mapped_column(default=False)
    reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, default=lambda: secrets.token_urlsafe(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    event: Mapped["Event"] = relationship(back_populates="rsvps")
    participant: Mapped["Participant"] = relationship(back_populates="rsvps")

class Setting(Base):
    __tablename__ = "settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True)
    value: Mapped[str] = mapped_column(String(500), nullable=True)
