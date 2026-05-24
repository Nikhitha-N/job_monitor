from datetime import datetime
from urllib.parse import urlparse

import requests


def _get_ashby_slug(url: str) -> str | None:
    path_parts = [p for p in urlparse(url).path.split("/") if p]

    if path_parts:
        return path_parts[0]

    return None


def scrape_ashby(company: dict) -> list[dict]:
    name = company.get("name", "Unknown")
    url = company.get("url", "")
    slug = _get_ashby_slug(url)

    if not slug:
        return []

    api_url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"

    try:
        response = requests.get(api_url, timeout=20)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return []

    jobs = []

    for job in data.get("jobs", []):
        title = job.get("title")
        job_url = job.get("jobUrl") or job.get("applyUrl")

        if not title or not job_url:
            continue

        location = ""
        if isinstance(job.get("location"), dict):
            location = job["location"].get("name", "")
        elif isinstance(job.get("location"), str):
            location = job.get("location")

        jobs.append(
            {
                "title": title,
                "url": job_url,
                "company": name,
                "location": location,
                "found_at": datetime.now().isoformat(),
                "source": "ashby",
            }
        )

    return jobs