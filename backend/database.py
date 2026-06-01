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
    from models import Provider, Event, Participant, RSVP  # noqa: F401
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(events)")).fetchall()]
        if "detail_url" not in cols:
            conn.execute(text("ALTER TABLE events ADD COLUMN detail_url VARCHAR(1000)"))
        if "description" not in cols:
            conn.execute(text("ALTER TABLE events ADD COLUMN description VARCHAR(2000)"))
        conn.commit()
