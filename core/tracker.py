"""
Tracks which job URLs have already been notified so we never send duplicates.
Uses a simple JSON file as a persistent store.
"""

import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "seen_jobs.json"


def _load() -> dict:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        try:
            return json.loads(DB_PATH.read_text())
        except json.JSONDecodeError:
            pass
    return {}


def _save(db: dict) -> None:
    DB_PATH.write_text(json.dumps(db, indent=2))


def filter_new(jobs: list[dict]) -> list[dict]:
    """Returns only jobs not seen before, and marks them as seen."""
    db = _load()
    new_jobs = []
    for job in jobs:
        url = job["url"]
        if url not in db:
            db[url] = {
                "title": job["title"],
                "company": job["company"],
                "first_seen": datetime.now().isoformat(),
            }
            new_jobs.append(job)

    if new_jobs:
        _save(db)
        logger.info(f"{len(new_jobs)} new job(s) to notify about.")
    else:
        logger.info("No new jobs since last run.")

    return new_jobs


def get_all_seen() -> dict:
    return _load()


def clear_database() -> None:
    """Reset seen jobs (useful for testing)."""
    _save({})
    logger.info("Seen-jobs database cleared.")
