"""
job_monitor/main.py
Run with:  python main.py
           python main.py --once     (single run, no loop — useful for cron)
           python main.py --check    (test Ollama + config, no scraping)
"""

import time
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import config
from core.loader import load_companies
from core.scraper import scrape_all
from core.tracker import filter_new
from core.ollama_classifier import OllamaClassifier
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


def build_classifier() -> OllamaClassifier:
    model = getattr(config, "OLLAMA_MODEL", None) if config.USE_OLLAMA else None
    return OllamaClassifier(model=model)


def run_once(classifier: OllamaClassifier):
    logger.info("=" * 60)
    logger.info("Starting job scan…")

    try:
        companies = load_companies(config.COMPANIES_FILE)
    except Exception as e:
        logger.error(f"Could not load companies file: {e}")
        return

    if not companies:
        logger.warning("No companies loaded. Check your file.")
        return

    all_jobs = scrape_all(companies, classifier)
    new_jobs = filter_new(all_jobs)

    if not new_jobs:
        logger.info("No new jobs since last run.")
        return

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


def check_mode():
    """Validate config and Ollama without scraping anything."""
    logger.info("--- Config Check ---")
    logger.info(f"Companies file : {config.COMPANIES_FILE}")
    logger.info(f"Notify email   : {config.NOTIFY_EMAIL}")
    logger.info(f"SMS enabled    : {config.NOTIFY_SMS}")
    logger.info(f"Interval       : {config.CHECK_INTERVAL_MINUTES} min")
    logger.info(f"Use Ollama     : {config.USE_OLLAMA}")
    if config.USE_OLLAMA:
        logger.info(f"Ollama model   : {getattr(config, 'OLLAMA_MODEL', 'auto-detect')}")

    logger.info("--- Ollama Status ---")
    clf = build_classifier()
    if clf.available:
        test_titles = [
            "Senior Data Scientist",
            "Machine Learning Engineer",
            "Software Engineer II",
            "Product Manager",
            "NLP Research Scientist",
        ]
        logger.info("Running test classifications:")
        for t in test_titles:
            result = clf.is_relevant(t)
            label = "[RELEVANT]" if result else "[SKIP]    "
            logger.info(f"  {label}  {t}")
    logger.info("--- Check complete ---")


def main():
    args = sys.argv[1:]

    if "--check" in args:
        check_mode()
        return

    # Build classifier once — reused across all runs
    classifier = build_classifier()

    if "--once" in args:
        run_once(classifier)
        return

    logger.info("Job Monitor started.")
    logger.info(f"Interval: every {config.CHECK_INTERVAL_MINUTES} minute(s). Ctrl+C to stop.")

    while True:
        try:
            run_once(classifier)
        except KeyboardInterrupt:
            logger.info("Stopped by user.")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)

        logger.info(f"Sleeping {config.CHECK_INTERVAL_MINUTES} min…")
        time.sleep(config.CHECK_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    main()
