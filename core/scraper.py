"""
core/scraper.py

Routes each company career URL through:
1. Platform/API adapter: Greenhouse, Lever, Ashby, Workday
2. Static requests + BeautifulSoup scraper
3. Playwright fallback for JavaScript-heavy pages
4. OllamaClassifier filtering
"""

import logging
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from core.adapters.greenhouse import scrape_greenhouse
from core.adapters.lever import scrape_lever
from core.adapters.ashby import scrape_ashby
from core.adapters.workday import scrape_workday
from core.adapters.playwright_fallback import scrape_with_playwright

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

JOB_PATH_PATTERN = re.compile(
    r"(job|career|position|opening|vacancy|role|requisition|req|apply)",
    re.I,
)


def fetch_page(url: str, timeout: int = 20) -> str | None:
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


def extract_candidate_links(html: str, base_url: str, company_name: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    candidates = []
    seen = set()

    for a in soup.find_all("a", href=True):
        title = a.get_text(" ", strip=True)
        href = a["href"]

        if not title or len(title) < 4 or len(title) > 180:
            continue

        full_url = urljoin(base_url, href)

        if full_url in seen:
            continue

        path = urlparse(full_url).path
        if not JOB_PATH_PATTERN.search(path) and not JOB_PATH_PATTERN.search(href):
            continue

        seen.add(full_url)

        candidates.append(
            {
                "title": title,
                "url": full_url,
                "company": company_name,
                "found_at": datetime.now().isoformat(),
                "source": "static",
            }
        )

    return candidates


def detect_platform(url: str) -> str:
    lowered = url.lower()

    if "greenhouse.io" in lowered:
        return "greenhouse"

    if "lever.co" in lowered:
        return "lever"

    if "ashbyhq.com" in lowered:
        return "ashby"

    if "myworkdayjobs.com" in lowered or "workdayjobs.com" in lowered:
        return "workday"

    return "generic"


def scrape_static(company: dict) -> list[dict]:
    name = company.get("name", "Unknown")
    url = company.get("url", "")

    html = fetch_page(url)

    if not html:
        return []

    return extract_candidate_links(html, url, name)


def scrape_company(company: dict, classifier) -> list[dict]:
    name = company.get("name", "Unknown")
    url = company.get("url", "")

    logger.info(f"Scraping {name} -> {url}")

    candidates = []
    platform = detect_platform(url)

    # 1. Platform-specific API adapters
    if platform == "greenhouse":
        candidates = scrape_greenhouse(company)
    elif platform == "lever":
        candidates = scrape_lever(company)
    elif platform == "ashby":
        candidates = scrape_ashby(company)
    elif platform == "workday":
        candidates = scrape_workday(company)

    if candidates:
        logger.info(f"Found {len(candidates)} candidate(s) using {platform} adapter")

    # 2. Static scraper fallback
    if not candidates:
        candidates = scrape_static(company)
        logger.info(f"Found {len(candidates)} candidate(s) using static scraper")

    # 3. Playwright fallback
    if not candidates:
        logger.info(f"No static/API candidates found for {name}. Trying Playwright...")
        candidates = scrape_with_playwright(company)
        logger.info(f"Found {len(candidates)} candidate(s) using Playwright")

    if not candidates:
        logger.info(f"No candidates found for {name}")
        return []

    # 4. Ollama / keyword classifier
    relevant = classifier.filter_jobs(candidates)
    logger.info(f"-> {len(relevant)} relevant role(s) at {name}")

    return relevant


def scrape_all(companies: list[dict], classifier) -> list[dict]:
    all_jobs = []

    for company in companies:
        try:
            all_jobs.extend(scrape_company(company, classifier))
        except Exception as e:
            logger.error(f"Failed scraping {company.get('name', 'Unknown')}: {e}", exc_info=True)

    return all_jobs



