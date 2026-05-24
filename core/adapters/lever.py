from datetime import datetime
from urllib.parse import urlparse

import requests


def _get_lever_slug(url: str) -> str | None:
    path_parts = [p for p in urlparse(url).path.split("/") if p]

    if path_parts:
        return path_parts[0]

    return None


def scrape_lever(company: dict) -> list[dict]:
    name = company.get("name", "Unknown")
    url = company.get("url", "")
    slug = _get_lever_slug(url)

    if not slug:
        return []

    api_url = f"https://api.lever.co/v0/postings/{slug}?mode=json"

    try:
        response = requests.get(api_url, timeout=20)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return []

    jobs = []

    for job in data:
        title = job.get("text")
        hosted_url = job.get("hostedUrl") or job.get("applyUrl")

        if not title or not hosted_url:
            continue

        categories = job.get("categories") or {}

        jobs.append(
            {
                "title": title,
                "url": hosted_url,
                "company": name,
                "location": categories.get("location", ""),
                "team": categories.get("team", ""),
                "commitment": categories.get("commitment", ""),
                "found_at": datetime.now().isoformat(),
                "source": "lever",
            }
        )

    return jobs