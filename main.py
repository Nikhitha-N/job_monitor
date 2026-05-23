"""
job_monitor/main.py
Run with:  python main.py
"""

import time
import logging
import sys
from pathlib import Path

# Make sure local imports work when called from any directory
sys.path.insert(0, str(Path(__file__).parent))

import config
from core.loader import load_companies
from core.scraper import scrape_all
from core.tracker import filter_new
from notifiers.email_notifier import send_email
from notifiers.sms_notifier import send_sms

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("job_monitor.log"),
    ],
)
logger = logging.getLogger(__name__)


def run_once():
    logger.info("=" * 60)
    logger.info("Starting job scan…")

    # 1. Load company list
    try:
        companies = load_companies(config.COMPANIES_FILE)
    except Exception as e:
        logger.error(f"Could not load companies file: {e}")
        return

    if not companies:
        logger.warning("No companies loaded. Check your file.")
        return

    # 2. Scrape
    all_jobs = scrape_all(companies)

    # 3. Filter to only new (unseen) jobs
    new_jobs = filter_new(all_jobs)

    if not new_jobs:
        logger.info("Nothing new. Will check again later.")
        return

    # 4. Notify
    logger.info(f"Sending notifications for {len(new_jobs)} new job(s)…")

    send_email(
        jobs=new_jobs,
        sender_email=config.GMAIL_ADDRESS,
        app_password=config.GMAIL_APP_PASS,
        recipient_email=config.NOTIFY_EMAIL,
    )

    if config.NOTIFY_SMS:
        send_sms(
            jobs=new_jobs,
            sender_email=config.GMAIL_ADDRESS,
            app_password=config.GMAIL_APP_PASS,
            phone_number=config.PHONE_NUMBER,
            carrier=config.CARRIER,
        )

    logger.info("Done.")


def main():
    logger.info("Job Monitor started.")
    logger.info(f"Checking every {config.CHECK_INTERVAL_MINUTES} minute(s).")
    logger.info(f"Company file: {config.COMPANIES_FILE}")
    logger.info(f"Notify: {config.NOTIFY_EMAIL}"
                + (f" + SMS {config.PHONE_NUMBER}" if config.NOTIFY_SMS else ""))

    while True:
        try:
            run_once()
        except KeyboardInterrupt:
            logger.info("Stopped by user.")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)

        wait_seconds = config.CHECK_INTERVAL_MINUTES * 60
        logger.info(f"Sleeping {config.CHECK_INTERVAL_MINUTES} min…")
        time.sleep(wait_seconds)


if __name__ == "__main__":
    main()
