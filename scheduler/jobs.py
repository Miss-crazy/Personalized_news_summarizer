"""
scheduler/jobs.py
APScheduler setup for the always-on ingestion loop.
 
Two loops (as discussed in the architecture):
  Fast loop  — runs every FAST_LOOP_INTERVAL_MINUTES (default 30)
               fetch → dedup → store
  Slow loop  — placeholder, will be wired in Phase 2
               re-cluster, refresh summaries
 
Run this file directly to start the scheduler:
    python -m scheduler.jobs
"""
 
import logging
import sys
import os
 
# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
 
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
 
from Personalized_news_summarizer.config.settings import FAST_LOOP_INTERVAL_MINUTES
from storage.database import init_db
from ingestion.pipeline import run_pipeline
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
 
 
def fast_loop_job():
    """Job function executed by the scheduler."""
    logger.info("Scheduler triggered fast loop")
    run_pipeline()
 
 
def start_scheduler():
    init_db()
 
    # Run once immediately on startup so we don't wait 30 min for first data
    logger.info("Running initial pipeline on startup...")
    run_pipeline()
 
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        fast_loop_job,
        trigger=IntervalTrigger(minutes=FAST_LOOP_INTERVAL_MINUTES),
        id="fast_loop",
        name="News ingestion fast loop",
        replace_existing=True,
    )
 
    logger.info(
        "Scheduler started — fast loop every %d minutes",
        FAST_LOOP_INTERVAL_MINUTES,
    )
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
 
 
if __name__ == "__main__":
    start_scheduler()
 