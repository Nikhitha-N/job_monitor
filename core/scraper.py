"""
Job scraper: fetches career pages and finds DS/ML/AI roles.
Uses BeautifulSoup for HTML parsing + optional local Ollama LLM for smarter filtering.
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import logging
from urllib.parse import urljoin, urlparse
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Keywords used when Ollama is NOT available ─────────────────────────────────
KEYWORDS = [
    "data science", "data scientist", "machine learning", "ml engineer",
    "ai engineer", "artificial intelligence", "deep learning", "nlp",
    "natural language processing", "computer vision", "data analyst",
    "analytics engineer", "mlops", "llm", "generative ai", "gen ai",
    "research scientist", "applied scientist", "data engineer",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


# ── Keyword-based filter (always available, no dependencies) ───────────────────
def keyword_match(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in KEYWORDS)


# ── Optional Ollama LLM filter ─────────────────────────────────────────────────
def ollama_match(title: str) -> bool | None:
    """Returns True/False if Ollama is running, else None (fallback to keywords)."""
    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": (
                    f'Is this job title related to data science, machine learning, or AI? '
                    f'Job title: "{title}". Reply with only YES or NO.'
                ),
                "stream": False,
            },
            timeout=10,
        )
        text = resp.json().get("response", "").strip().upper()
        return "YES" in text
    except Exception:
        return None  # Ollama not available


def is_relevant(title: str, use_ollama: bool = True) -> bool:
    if use_ollama:
        result = ollama_match(title)
        if result is not None:
            return result
    return keyword_match(title)


# ── HTML fetching ──────────────────────────────────────────────────────────────
def fetch_page(url: str, timeout: int = 15) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


# ── Generic job link extractor ─────────────────────────────────────────────────
def extract_jobs(html: str, base_url: str) -> list[dict]:
    """
    Heuristic extraction: find <a> tags whose text looks like a job title
    and whose href points to a job posting.
    """
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    seen = set()

    job_path_pattern = re.compile(
        r"(job|career|position|opening|vacancy|role|requisition|req)", re.I
    )

    for a in soup.find_all("a", href=True):
        title = a.get_text(strip=True)
        href = a["href"]

        if not title or len(title) < 4 or len(title) > 150:
            continue

        full_url = urljoin(base_url, href)
        if full_url in seen:
            continue

        # Only follow links that look like job postings
        path = urlparse(full_url).path
        if not job_path_pattern.search(path) and not job_path_pattern.search(href):
            continue

        if is_relevant(title):
            seen.add(full_url)
            jobs.append(
                {
                    "title": title,
                    "url": full_url,
                    "company": urlparse(base_url).netloc.replace("www.", ""),
                    "found_at": datetime.now().isoformat(),
                }
            )

    return jobs


# ── Main scrape function ───────────────────────────────────────────────────────
def scrape_company(company: dict) -> list[dict]:
    """
    company = {"name": "Google", "url": "https://careers.google.com/jobs"}
    """
    name = company.get("name", "Unknown")
    url = company.get("url", "")

    logger.info(f"Scraping {name} → {url}")
    html = fetch_page(url)
    if not html:
        return []

    jobs = extract_jobs(html, url)
    logger.info(f"  Found {len(jobs)} relevant posting(s) at {name}")
    return jobs


def scrape_all(companies: list[dict]) -> list[dict]:
    all_jobs = []
    for company in companies:
        all_jobs.extend(scrape_company(company))
    return all_jobs
