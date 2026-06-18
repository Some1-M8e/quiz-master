from fastapi import APIRouter, BackgroundTasks
from database import SessionLocal

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/scraper/run", status_code=200)
def run_scraper_now(background_tasks: BackgroundTasks):
    from scraper import run_scraper

    def _run():
        db = SessionLocal()
        try:
            run_scraper(db)
        finally:
            db.close()

    background_tasks.add_task(_run)
    return {"message": "Scraper gestartet"}


@router.post("/booking/run", status_code=200)
def run_booking_now():
    from scheduler import job_booking_logic

    job_booking_logic()
    return {"message": "Buchungslogik ausgeführt"}


@router.post("/scheduler/start", status_code=200)
def start_scheduler():
    from scheduler import start_scheduler as _start

    _start()
    return {"message": "Scheduler gestartet"}
