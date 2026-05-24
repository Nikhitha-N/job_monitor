from datetime import datetime
from urllib.parse import urlparse

import requests


HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Content-Type": "application/json",
}


def _parse_workday_url(url: str):
    parsed = urlparse(url)
    host = parsed.netloc
    path_parts = [p for p in parsed.path.split("/") if p]

    site = None

    for part in path_parts:
        if "job" in part.lower() or "career" in part.lower():
            site = part
            break

    if not site and path_parts:
        site = path_parts[-1]

    return host, site


def scrape_workday(company: dict) -> list[dict]:
    name = company.get("name", "Unknown")
    url = company.get("url", "")

    host, site = _parse_workday_url(url)

    if not host or not site:
        return []

    api_url = f"https://{host}/wday/cxs/{host.split('.')[0]}/{site}/jobs"

    payload = {
        "appliedFacets": {},
        "limit": 50,
        "offset": 0,
        "searchText": "",
    }

    try:
        response = requests.post(api_url, headers=HEADERS, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return []

    jobs = []

    for job in data.get("jobPostings", []):
        title = job.get("title")
        external_path = job.get("externalPath")

        if not title or not external_path:
            continue

        job_url = f"https://{host}{external_path}"

        locations = job.get("locationsText") or ""

        jobs.append(
            {
                "title": title,
                "url": job_url,
                "company": name,
                "location": locations,
                "found_at": datetime.now().isoformat(),
                "source": "workday",
            }
        )

    return jobs