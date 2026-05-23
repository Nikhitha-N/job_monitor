# ─────────────────────────────────────────────────────────────────────────────
# job_monitor/config.py  —  Fill this in before running
# ─────────────────────────────────────────────────────────────────────────────

# ── Path to your company list file ───────────────────────────────────────────
# Supported formats: .csv | .html | .pdf
# See README.md for the expected format of each.
COMPANIES_FILE = "companies.csv"   # ← change to your file path


# ── Notification settings ─────────────────────────────────────────────────────
# Gmail account you'll send FROM (enable 2-FA, then create an App Password at
# https://myaccount.google.com/apppasswords )
GMAIL_ADDRESS   = "nikhitha0613@gmail.com"     # ← your Gmail
GMAIL_APP_PASS  = "xoca ibpr dgxl vxfj"      # ← 16-char App Password (spaces ok)

# Email to receive alerts (can be the same Gmail, or any address)
NOTIFY_EMAIL    = "nikhitha0613@gmail.com"   # ← where to receive email alerts

# SMS alerts (optional — leave blank to disable)
NOTIFY_SMS      = False           # ← set True to enable SMS
PHONE_NUMBER    = "3527093513"    # ← 10-digit US number (digits only)
CARRIER         = "tmobile"       # ← att | tmobile | verizon | sprint |
                                  #    boost | cricket | metro | uscellular | fi


# ── Schedule ──────────────────────────────────────────────────────────────────
# How often to check (in minutes). 60 = once per hour.
CHECK_INTERVAL_MINUTES = 30


# ── AI filtering (optional) ───────────────────────────────────────────────────
# If True, the monitor tries to use a local Ollama LLM (llama3) for smarter
# job-title classification.  Falls back to keyword matching if Ollama isn't running.
# Install Ollama: https://ollama.com  then run: ollama pull llama3
USE_OLLAMA = False
