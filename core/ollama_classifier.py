"""
core/ollama_classifier.py
─────────────────────────
Full Ollama integration for job-title classification.

Features:
  - Auto-detects which models you have pulled (prefers best available)
  - Batch classification — sends all titles in ONE prompt (much faster)
  - Health check on startup with clear error messages
  - Confidence-aware: the LLM also returns a reason you can log
  - Graceful fallback to keyword matching if Ollama is unreachable
"""

import requests
import json
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

OLLAMA_BASE = "http://localhost:11434"

# Preferred model order — first one found wins
PREFERRED_MODELS = [
    "llama3",
    "llama3.1",
    "llama3.2",
    "llama3:8b",
    "llama3:70b",
    "mistral",
    "mistral-nemo",
    "gemma2",
    "gemma2:9b",
    "phi3",
    "phi3.5",
    "qwen2.5",
    "deepseek-r1",
]

# ── Keywords fallback (used if Ollama is down) ─────────────────────────────────
KEYWORDS = [
    "data science", "data scientist", "machine learning", "ml engineer",
    "ai engineer", "artificial intelligence", "deep learning", "nlp",
    "natural language processing", "computer vision", "data analyst",
    "analytics engineer", "mlops", "llm", "generative ai", "gen ai",
    "research scientist", "applied scientist", "data engineer",
    "quantitative", "statistician", "reinforcement learning",
]

def keyword_match(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in KEYWORDS)


# ── Health check ───────────────────────────────────────────────────────────────
def check_ollama_running() -> bool:
    """Ping Ollama and return True if it's up."""
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def get_available_models() -> list[str]:
    """Returns list of pulled model names."""
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        data = r.json()
        return [m["name"].split(":")[0] for m in data.get("models", [])]
    except Exception:
        return []


def pick_best_model(available: list[str]) -> Optional[str]:
    """Pick the best model from what's installed."""
    for preferred in PREFERRED_MODELS:
        for avail in available:
            if preferred.lower() in avail.lower():
                return avail
    return available[0] if available else None


# ── Startup validation ─────────────────────────────────────────────────────────
def validate_ollama(configured_model: Optional[str] = None) -> dict:
    """
    Call this at startup. Returns:
      { "ok": bool, "model": str or None, "message": str }
    """
    if not check_ollama_running():
        return {
            "ok": False,
            "model": None,
            "message": (
                "[ERROR] Ollama is not running.\n"
                "   Start it with:  ollama serve\n"
                "   Install from:   https://ollama.com\n"
                "   Falling back to keyword matching."
            ),
        }

    available = get_available_models()
    if not available:
        return {
            "ok": False,
            "model": None,
            "message": (
                "[ERROR] Ollama is running but no models are pulled.\n"
                "   Run:  ollama pull llama3\n"
                "   Falling back to keyword matching."
            ),
        }

    if configured_model and configured_model in available:
        model = configured_model
    else:
        model = pick_best_model(available)
        if configured_model:
            logger.warning(
                f"Model '{configured_model}' not found. "
                f"Using '{model}' instead. Available: {available}"
            )

    return {
        "ok": True,
        "model": model,
        "message": f"[OK] Ollama ready -- using model: {model}  (available: {', '.join(available)})",
    }


# ── Single title classification ────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are a job classifier. Your only job is to decide whether a given job title \
is related to Data Science, Machine Learning, or Artificial Intelligence.

Relevant roles include (but are not limited to):
- Data Scientist, Data Analyst, Data Engineer
- Machine Learning Engineer, ML Ops, AI Engineer
- Research Scientist, Applied Scientist
- NLP Engineer, Computer Vision Engineer
- LLM Engineer, Generative AI, Prompt Engineer
- Quantitative Analyst/Researcher
- Deep Learning, Reinforcement Learning roles
- Analytics Engineer, BI Engineer (if data-focused)

NOT relevant: Software Engineer (general), Product Manager, Sales, Marketing, \
Finance, HR, Legal, DevOps (unless AI-infra), unless the title explicitly \
mentions data/ML/AI.

Respond ONLY with valid JSON: {"relevant": true/false, "reason": "<one short sentence>"}
Do not add any text before or after the JSON.
"""

def classify_title(title: str, model: str, timeout: int = 15) -> tuple[bool, str]:
    """
    Classify a single job title using Ollama.
    Returns (is_relevant: bool, reason: str).
    Falls back to keyword matching on any error.
    """
    prompt = f'Job title: "{title}"'
    try:
        resp = requests.post(
            f"{OLLAMA_BASE}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "options": {"temperature": 0},  # deterministic
            },
            timeout=timeout,
        )
        raw = resp.json()["message"]["content"].strip()

        # Strip markdown code fences if model wraps output
        raw = raw.strip("`").strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()

        result = json.loads(raw)
        return bool(result.get("relevant", False)), result.get("reason", "")

    except json.JSONDecodeError:
        logger.debug(f"JSON parse failed for title '{title}', falling back to keywords")
        return keyword_match(title), "keyword fallback (JSON parse error)"
    except Exception as e:
        logger.debug(f"Ollama error for '{title}': {e} — keyword fallback")
        return keyword_match(title), "keyword fallback (Ollama error)"


# ── Batch classification (faster: one request per N titles) ───────────────────
BATCH_SYSTEM = """\
You are a job classifier. Classify each job title as relevant or not to \
Data Science, Machine Learning, or AI.

Relevant: Data Scientist, ML Engineer, AI Engineer, Data Analyst, Data Engineer, \
NLP, Computer Vision, LLM, Research Scientist, Applied Scientist, MLOps, \
Generative AI, Quantitative Researcher, Analytics Engineer, Deep Learning, etc.

NOT relevant: general Software Engineer, Product Manager, Sales, HR, Marketing, \
Finance, Legal — unless the title explicitly mentions data/ML/AI.

You will receive a JSON array of {"id": int, "title": str} objects.
Respond ONLY with a JSON array: [{"id": int, "relevant": bool}, ...]
No extra text.
"""

def classify_batch(titles: list[str], model: str, batch_size: int = 20, timeout: int = 60) -> list[bool]:
    """
    Classify a list of titles in batches.
    Returns a list of booleans (same order as input).
    Falls back per-item to keywords on error.
    """
    results = [False] * len(titles)

    for start in range(0, len(titles), batch_size):
        chunk = titles[start : start + batch_size]
        payload = [{"id": i, "title": t} for i, t in enumerate(chunk)]

        try:
            resp = requests.post(
                f"{OLLAMA_BASE}/api/chat",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": BATCH_SYSTEM},
                        {"role": "user", "content": json.dumps(payload)},
                    ],
                    "stream": False,
                    "options": {"temperature": 0},
                },
                timeout=timeout,
            )
            raw = resp.json()["message"]["content"].strip().strip("`").strip()
            if raw.startswith("json"):
                raw = raw[4:].strip()

            batch_results = json.loads(raw)
            for item in batch_results:
                idx = start + item["id"]
                if idx < len(results):
                    results[idx] = bool(item.get("relevant", False))

            logger.info(
                f"  Batch {start//batch_size + 1}: classified {len(chunk)} titles — "
                f"{sum(r['relevant'] for r in batch_results if isinstance(r.get('relevant'), bool))} relevant"
            )

        except Exception as e:
            logger.warning(f"Batch classification failed ({e}), falling back to keywords for this batch")
            for i, title in enumerate(chunk):
                results[start + i] = keyword_match(title)

        time.sleep(0.1)  # small pause between batches to not overwhelm Ollama

    return results


# ── Main public interface ──────────────────────────────────────────────────────
class OllamaClassifier:
    """
    Stateful classifier — validates Ollama once at init, then classifies jobs.
    Usage:
        clf = OllamaClassifier(model="llama3")
        relevant = clf.filter_jobs(list_of_job_dicts)
    """

    def __init__(self, model: Optional[str] = None):
        status = validate_ollama(model)
        logger.info(status["message"])
        self.available = status["ok"]
        self.model = status["model"]

    def is_relevant(self, title: str) -> bool:
        """Classify a single title."""
        if not self.available:
            return keyword_match(title)
        relevant, reason = classify_title(title, self.model)
        logger.debug(f"  '{title}' -> {'[YES]' if relevant else '[NO]'}  ({reason})")
        return relevant

    def filter_jobs(self, jobs: list[dict]) -> list[dict]:
        """
        Given a list of job dicts (must have 'title' key),
        return only those classified as relevant.
        Uses batch mode for efficiency.
        """
        if not jobs:
            return []

        titles = [j["title"] for j in jobs]

        if self.available:
            logger.info(f"Classifying {len(titles)} job title(s) with Ollama ({self.model})…")
            relevance = classify_batch(titles, self.model)
        else:
            logger.info("Ollama unavailable — using keyword matching…")
            relevance = [keyword_match(t) for t in titles]

        filtered = [job for job, rel in zip(jobs, relevance) if rel]
        logger.info(f"  {len(filtered)}/{len(jobs)} titles classified as relevant.")
        return filtered
