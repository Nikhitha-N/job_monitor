from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin, urlparse
from datetime import datetime
import re


JOB_PATH_PATTERN = re.compile(
    r"(job|career|position|opening|vacancy|role|requisition|req|apply)", re.I
)


def scrape_with_playwright(company: dict) -> list[dict]:
    name = company.get("name", "Unknown")
    url = company.get("url", "")
    candidates = []
    seen = set()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)
            html = page.content()
            browser.close()

    except Exception as e:
        print(f"Playwright failed for {name}: {e}")
        return []

    soup = BeautifulSoup(html, "html.parser")

    for a in soup.find_all("a", href=True):
        title = a.get_text(" ", strip=True)
        href = a["href"]

        if not title or len(title) < 4 or len(title) > 150:
            continue

        full_url = urljoin(url, href)

        if full_url in seen:
            continue

        path = urlparse(full_url).path
        if not JOB_PATH_PATTERN.search(path) and not JOB_PATH_PATTERN.search(href):
            continue

        seen.add(full_url)

        candidates.append({
            "title": title,
            "url": full_url,
            "company": name,
            "found_at": datetime.now().isoformat()
        })

    return candidates