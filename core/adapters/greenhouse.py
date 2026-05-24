from datetime import datetime
from urllib.parse import urlparse

import requests


def _get_greenhouse_slug(url: str) -> str | None:
    path_parts = [p for p in urlparse(url).path.split("/") if p]

    if path_parts:
        return path_parts[0]

    return None


def scrape_greenhouse(company: dict) -> list[dict]:
    name = company.get("name", "Unknown")
    url = company.get("url", "")
    slug = _get_greenhouse_slug(url)

    if not slug:
        return []

    api_url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"

    try:
        response = requests.get(api_url, timeout=20)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return []

    jobs = []

    for job in data.get("jobs", []):
        title = job.get("title")
        absolute_url = job.get("absolute_url")

        if not title or not absolute_url:
            continue

        jobs.append(
            {
                "title": title,
                "url": absolute_url,
                "company": name,
                "location": ", ".join(
                    office.get("name", "") for office in job.get("offices", []) if office.get("name")
                ),
                "found_at": datetime.now().isoformat(),
                "source": "greenhouse",
            }
        )

    return jobs