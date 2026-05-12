"""
ingestion/pipeline.py
Orchestrates one full ingestion run: GNews → RSS → Scraper.
 
Call run_pipeline() from the scheduler or directly from the CLI.
Returns a combined summary for logging / monitoring.
"""
 
import logging
 
from storage.database import article_count
from ingestion.gnews_collector import collect_gnews
from ingestion.rss_collector import collect_rss
from ingestion.scraper import collect_scraped
 
logger = logging.getLogger(__name__)
 
 
def run_pipeline() -> dict:
    """
    Run all three collectors in sequence.
    Failures in one collector don't abort the others.
    Returns a summary dict with per-source stats + DB totals.
    """
    logger.info("=" * 50)
    logger.info("Ingestion pipeline starting")
    logger.info("=" * 50)
 
    results = {}
 
    # ── 1. GNews ──────────────────────────────────────────
    logger.info("--- GNews API ---")
    try:
        results["gnews"] = collect_gnews()
    except Exception as exc:
        logger.error("GNews collector crashed: %s", exc, exc_info=True)
        results["gnews"] = {"error": str(exc)}
 
    # ── 2. RSS ────────────────────────────────────────────
    logger.info("--- RSS Feeds ---")
    try:
        results["rss"] = collect_rss()
    except Exception as exc:
        logger.error("RSS collector crashed: %s", exc, exc_info=True)
        results["rss"] = {"error": str(exc)}
 
    # ── 3. Scraper ────────────────────────────────────────
    logger.info("--- Web Scraper ---")
    try:
        results["scraped"] = collect_scraped()
    except Exception as exc:
        logger.error("Scraper crashed: %s", exc, exc_info=True)
        results["scraped"] = {"error": str(exc)}
 
    # ── Summary ───────────────────────────────────────────
    counts = article_count()
    results["db"] = counts
    logger.info(
        "Pipeline complete — DB now has %d articles (%d unprocessed)",
        counts["total"],
        counts["unprocessed"],
    )
    logger.info("=" * 50)
 
    return results
 