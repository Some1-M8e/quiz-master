from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import settings

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from models import Provider, Event, Participant, RSVP, Setting  # noqa: F401
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        # Events: detail_url, description, status, source, capacity
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(events)")).fetchall()]
        if "detail_url" not in cols:
            conn.execute(text("ALTER TABLE events ADD COLUMN detail_url VARCHAR(1000)"))
        if "description" not in cols:
            conn.execute(text("ALTER TABLE events ADD COLUMN description VARCHAR(2000)"))
        if "status" not in cols:
            conn.execute(text("ALTER TABLE events ADD COLUMN status VARCHAR(20) DEFAULT 'neu'"))
        if "source" not in cols:
            conn.execute(text("ALTER TABLE events ADD COLUMN source VARCHAR(20) DEFAULT 'scraper'"))
        if "capacity" not in cols:
            conn.execute(text("ALTER TABLE events ADD COLUMN capacity INTEGER"))
        # Participants: notifications_enabled
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(participants)")).fetchall()]
        if "notifications_enabled" not in cols:
            conn.execute(text("ALTER TABLE participants ADD COLUMN notifications_enabled INTEGER DEFAULT 1"))
        # RSVP: selected, reminder_sent_at, token
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(rsvps)")).fetchall()]
        if "selected" not in cols:
            conn.execute(text("ALTER TABLE rsvps ADD COLUMN selected INTEGER DEFAULT 1"))
        if "reminder_sent_at" not in cols:
            conn.execute(text("ALTER TABLE rsvps ADD COLUMN reminder_sent_at DATETIME"))
        if "token" not in cols:
            conn.execute(text("ALTER TABLE rsvps ADD COLUMN token VARCHAR(50)"))
        # Settings table: create if not exists
        try:
            conn.execute(text("SELECT * FROM settings LIMIT 1"))
        except:
            conn.execute(text("CREATE TABLE IF NOT EXISTS settings (key VARCHAR(100) PRIMARY KEY, value TEXT)"))
        conn.commit()
