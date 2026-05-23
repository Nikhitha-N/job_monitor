"""
Loads the list of companies from a CSV, PDF, or HTML file.
Expected columns / content: company name + career page URL.
"""

import csv
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# ── CSV ────────────────────────────────────────────────────────────────────────
def _load_csv(path: str) -> list[dict]:
    """
    Accepts any CSV with columns that look like name/company and url/link/career.
    Also handles a plain two-column CSV with no header (name, url).
    """
    companies = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        sample = f.read(2048)
        f.seek(0)
        has_header = csv.Sniffer().has_header(sample)
        reader = csv.DictReader(f) if has_header else csv.reader(f)

        for row in reader:
            if isinstance(row, dict):
                keys = [k.lower().strip() for k in row.keys()]
                name_key = next((k for k in keys if "name" in k or "company" in k), keys[0])
                url_key = next((k for k in keys if "url" in k or "link" in k or "career" in k or "site" in k), keys[1])
                orig_keys = list(row.keys())
                name = row[orig_keys[keys.index(name_key)]].strip()
                url = row[orig_keys[keys.index(url_key)]].strip()
            else:
                if len(row) < 2:
                    continue
                name, url = row[0].strip(), row[1].strip()

            if name and url:
                if not url.startswith("http"):
                    url = "https://" + url
                companies.append({"name": name, "url": url})

    return companies


# ── HTML ───────────────────────────────────────────────────────────────────────
def _load_html(path: str) -> list[dict]:
    """Parses an HTML file and extracts all links as (link text → href) pairs."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        raise ImportError("Run: pip install beautifulsoup4")

    with open(path, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    companies = []
    for a in soup.find_all("a", href=True):
        name = a.get_text(strip=True)
        url = a["href"]
        if name and url.startswith("http"):
            companies.append({"name": name, "url": url})

    return companies


# ── PDF ────────────────────────────────────────────────────────────────────────
def _load_pdf(path: str) -> list[dict]:
    """
    Extracts text from a PDF and finds lines that look like 'Name, URL'.
    Requires: pip install pdfplumber
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("Run: pip install pdfplumber")

    url_re = re.compile(r"https?://\S+")
    companies = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                urls = url_re.findall(line)
                if not urls:
                    continue
                url = urls[0].rstrip(".,;)")
                # everything before the URL is considered the company name
                name = url_re.sub("", line).strip(" ,:-")
                if not name:
                    name = url  # fallback: use URL as name
                companies.append({"name": name, "url": url})

    return companies


# ── Public loader ──────────────────────────────────────────────────────────────
def load_companies(file_path: str) -> list[dict]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = path.suffix.lower()
    if suffix == ".csv":
        companies = _load_csv(file_path)
    elif suffix in (".htm", ".html"):
        companies = _load_html(file_path)
    elif suffix == ".pdf":
        companies = _load_pdf(file_path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}  (use .csv, .html, or .pdf)")

    logger.info(f"Loaded {len(companies)} companies from {path.name}")
    return companies
