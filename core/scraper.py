"""
core/scraper.py
─────────────────
Fetches career pages and extracts candidate job links.
Classification is now handled by OllamaClassifier (ollama_classifier.py).
"""

import requests
from bs4 import BeautifulSoup
import re
import logging
from urllib.parse import urljoin, urlparse
from datetime import datetime

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

JOB_PATH_PATTERN = re.compile(
    r"(job|career|position|opening|vacancy|role|requisition|req|apply)", re.I
)


def fetch_page(url: str, timeout: int = 15) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


def extract_candidate_links(html: str, base_url: str) -> list[dict]:
    """
    Extract ALL links that look like job postings — before any classification.
    Returns raw candidates for the classifier to filter.
    """
    soup = BeautifulSoup(html, "html.parser")
    candidates = []
    seen = set()

    for a in soup.find_all("a", href=True):
        title = a.get_text(strip=True)
        href = a["href"]

        if not title or len(title) < 4 or len(title) > 150:
            continue

        full_url = urljoin(base_url, href)
        if full_url in seen:
            continue

        path = urlparse(full_url).path
        if not JOB_PATH_PATTERN.search(path) and not JOB_PATH_PATTERN.search(href):
            continue

        seen.add(full_url)
        candidates.append({
            "title": title,
            "url": full_url,
            "company": urlparse(base_url).netloc.replace("www.", ""),
            "found_at": datetime.now().isoformat(),
        })

    return candidates


def scrape_company(company: dict, classifier) -> list[dict]:
    """
    Scrape one company's career page.
    `classifier` must have a .filter_jobs(list[dict]) -> list[dict] method.
    """
    name = company.get("name", "Unknown")
    url = company.get("url", "")

    logger.info(f"Scraping {name} → {url}")
    html = fetch_page(url)
    if not html:
        logger.warning(f"  Could not fetch page for {name}")
        return []

    candidates = extract_candidate_links(html, url)
    logger.info(f"  Found {len(candidates)} candidate link(s) at {name}")

    if not candidates:
        return []

    relevant = classifier.filter_jobs(candidates)
    logger.info(f"  → {len(relevant)} relevant DS/ML/AI role(s) at {name}")
    return relevant


def scrape_all(companies: list[dict], classifier) -> list[dict]:
    all_jobs = []
    for company in companies:
        all_jobs.extend(scrape_company(company, classifier))
    return all_jobs
