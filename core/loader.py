import csv
from pathlib import Path


def load_companies(file_path: str) -> list[dict]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Companies file not found: {file_path}")

    companies = []

    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=",")

        if not reader.fieldnames:
            raise ValueError("CSV file is empty or missing header row")

        required_cols = {"name", "url"}
        actual_cols = {col.strip().lower() for col in reader.fieldnames}

        if not required_cols.issubset(actual_cols):
            raise ValueError("CSV must contain columns: name,url")

        for row in reader:
            name = (row.get("name") or "").strip()
            url = (row.get("url") or "").strip()

            if not name or not url:
                continue

            if name.lower() == "name" or url.lower() in {"url", "https://url"}:
                continue

            companies.append({
                "name": name,
                "url": url
            })

    return companies