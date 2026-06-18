import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import providers, participants, events, rsvps, admin, auth

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    import threading
    from scheduler import start_scheduler

    def _start():
        start_scheduler()

    threading.Thread(target=_start, daemon=True).start()
    yield


app = FastAPI(title="Quiz-Master", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(providers.router)
app.include_router(participants.router)
app.include_router(events.router)
app.include_router(rsvps.router)
app.include_router(admin.router)
app.include_router(auth.router)
