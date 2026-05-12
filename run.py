"""
run.py
CLI entry point for Phase 1.

Usage
-----
  # Run pipeline once and exit (good for testing)
  python run.py --once

  # Start the scheduler (runs forever, re-fetches every 30 min)
  python run.py --scheduler

  # Print DB stats
  python run.py --stats
"""

import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from storage.database import init_db, article_count, fetch_unprocessed
from ingestion.pipeline import run_pipeline


def cmd_once():
    init_db()
    results = run_pipeline()
    print("\nRun complete.")
    db = results.get("db", {})
    print(f"  Total articles in DB  : {db.get('total', '?')}")
    print(f"  Unprocessed (ready)   : {db.get('unprocessed', '?')}")


def cmd_stats():
    init_db()
    counts = article_count()
    print(f"Total articles   : {counts['total']}")
    print(f"Unprocessed      : {counts['unprocessed']}")
    articles = fetch_unprocessed(limit=5)
    if articles:
        print("\nMost recent unprocessed articles:")
        for a in articles:
            print(f"  [{a['source']}] {a['title'][:70]}")


def cmd_scheduler():
    from Personalized_news_summarizer.scheduler.jobs import start_scheduler
    start_scheduler()


def main():
    parser = argparse.ArgumentParser(description="Phase 1 — News Ingestion")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--once",      action="store_true", help="Run pipeline once and exit")
    group.add_argument("--scheduler", action="store_true", help="Start continuous scheduler")
    group.add_argument("--stats",     action="store_true", help="Print DB stats")
    args = parser.parse_args()

    if args.once:
        cmd_once()
    elif args.scheduler:
        cmd_scheduler()
    elif args.stats:
        cmd_stats()


if __name__ == "__main__":
    main()