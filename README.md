# 🤖 Job Monitor — DS/ML/AI Career Alert System

Runs **locally on your machine**, scrapes company career pages, and notifies you
by **email and/or SMS** whenever a Data Science, ML, or AI role appears.
**Completely free. No cloud. No API keys.**

---

## 📁 Project Structure

```
job_monitor/
├── main.py                  ← run this
├── config.py                ← your settings (edit before running)
├── companies.csv            ← your list of companies to watch
├── requirements.txt
├── core/
│   ├── scraper.py           ← fetches & parses career pages
│   ├── loader.py            ← reads your CSV/PDF/HTML file
│   └── tracker.py           ← remembers seen jobs (no duplicates)
├── notifiers/
│   ├── email_notifier.py    ← Gmail SMTP
│   └── sms_notifier.py      ← free carrier gateway SMS
└── data/
    └── seen_jobs.json       ← auto-created; stores seen job URLs
```

---

## ⚡ Quick Start (5 steps)

### Step 1 — Install Python dependencies

```bash
cd job_monitor
pip install -r requirements.txt
```

### Step 2 — Add your companies

Edit `companies.csv`:

```csv
name,url
Google,https://careers.google.com/jobs/results/?q=data+scientist
Meta,https://www.metacareers.com/jobs?q=machine+learning
Stripe,https://stripe.com/jobs/search?q=data
```

Or supply a **PDF** (one line per company: `Company Name  https://careers.example.com`)
or an **HTML** file (just `<a href="...">Company Name</a>` links).

Then update `config.py`:
```python
COMPANIES_FILE = "companies.csv"   # or "companies.pdf" / "companies.html"
```

### Step 3 — Set up Gmail (free, 2 minutes)

1. Go to your Google Account → **Security** → turn on **2-Step Verification**
2. Search for **"App Passwords"** in your Google Account settings
3. Create a new App Password → name it "Job Monitor" → copy the 16-char code
4. Edit `config.py`:

```python
GMAIL_ADDRESS  = "you@gmail.com"
GMAIL_APP_PASS = "abcd efgh ijkl mnop"   # the App Password
NOTIFY_EMAIL   = "you@gmail.com"          # where to receive alerts
```

### Step 4 — (Optional) Enable SMS

Find your carrier gateway from this list:

| Carrier    | Gateway                         |
|------------|---------------------------------|
| AT&T       | `att`  → `number@txt.att.net`   |
| T-Mobile   | `tmobile` → `number@tmomail.net`|
| Verizon    | `verizon` → `number@vtext.com`  |
| Sprint     | `sprint`                        |
| Boost      | `boost`                         |
| Cricket    | `cricket`                       |
| Metro PCS  | `metro`                         |
| Google Fi  | `fi`                            |

Edit `config.py`:

```python
NOTIFY_SMS   = True
PHONE_NUMBER = "5551234567"   # digits only
CARRIER      = "tmobile"      # see table above
```

### Step 5 — Run it!

```bash
python main.py
```

The monitor will:
- Immediately scan all companies
- Email/SMS you about any matching jobs
- Wait 60 minutes (configurable in `config.py`)
- Repeat forever (Ctrl+C to stop)

---

## ⏰ Run Automatically in the Background

### Mac / Linux — cron job

```bash
crontab -e
```
Add this line to check every hour:
```
0 * * * * cd /path/to/job_monitor && python main.py --once >> job_monitor.log 2>&1
```

> **Tip**: Add `--once` support by editing `main.py`'s `if __name__ == "__main__":`
> block to call `run_once()` instead of `main()` when `--once` is in `sys.argv`.

### Windows — Task Scheduler

1. Open **Task Scheduler** → Create Basic Task
2. Trigger: Daily, repeat every 1 hour
3. Action: Start a program → `python`
4. Arguments: `C:\path\to\job_monitor\main.py`

---

## 🧠 Optional: Smarter AI Filtering with Ollama (free, local LLM)

Instead of just keyword matching, you can use a local LLM to intelligently
decide if a job title is relevant.

```bash
# Install Ollama: https://ollama.com
brew install ollama        # Mac
# or download installer from https://ollama.com/download

ollama pull llama3         # download the model (~4 GB)
ollama serve               # start the server (runs on localhost:11434)
```

Then in `config.py`:
```python
USE_OLLAMA = True
```

The scraper will ask the LLM "Is this job title related to DS/ML/AI?" for every
posting and only alert you on `YES`. Falls back to keyword matching if Ollama
isn't running.

---

## 📋 Company File Formats

### CSV (recommended)
```csv
name,url
Google,https://careers.google.com/jobs/results/?q=data+scientist
Meta,https://www.metacareers.com/jobs?q=machine+learning
```

### HTML
```html
<a href="https://careers.google.com">Google</a>
<a href="https://www.metacareers.com/jobs">Meta</a>
```

### PDF
Plain text PDF, one company per line:
```
Google  https://careers.google.com/jobs/results/?q=data+scientist
Meta    https://www.metacareers.com/jobs?q=machine+learning
```

---

## 🔧 Troubleshooting

| Problem | Fix |
|---------|-----|
| Gmail auth error | Make sure you're using an **App Password**, not your regular password |
| No jobs found | Some sites use JavaScript to load jobs — add `?q=data+science` to the URL to pre-filter |
| SMS not arriving | Check your carrier gateway and that the phone number has no spaces/dashes |
| Too many/few results | Edit `KEYWORDS` list in `core/scraper.py` |

---

## 📝 Notes

- The monitor stores seen jobs in `data/seen_jobs.json` — delete this file to
  re-send all current jobs (useful for testing).
- Some career pages are JavaScript-heavy (React SPAs). If a company returns 0 jobs,
  try finding the direct API URL the page uses (check Network tab in browser DevTools)
  and use that instead. Many Greenhouse/Lever/Workday boards have static JSON endpoints.
- Common ATS static endpoints:
  - **Greenhouse**: `https://boards-api.greenhouse.io/v1/boards/{slug}/jobs`
  - **Lever**: `https://api.lever.co/v0/postings/{slug}?mode=json`
  - **Workday**: check Network tab for `*.workday.com/*/jobs` XHR requests

---

## ✅ Completely Free

| Component | Cost |
|-----------|------|
| Python scraper | Free |
| Gmail SMTP | Free |
| SMS via email gateway | Free |
| Ollama local LLM | Free |
| Running on your machine | Free |
