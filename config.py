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


# ── Ollama AI Classifier ──────────────────────────────────────────────────────
# Ollama MUST be installed and running: https://ollama.com
#   Install:  https://ollama.com/download
#   Start:    ollama serve
#   Pull a model (pick ONE):
#     ollama pull llama3          ← recommended, fast (~4 GB)
#     ollama pull llama3.1        ← slightly newer
#     ollama pull mistral         ← good alternative (~4 GB)
#     ollama pull gemma2          ← Google's model (~5 GB)
#     ollama pull phi3            ← lighter, faster (~2 GB)
#
# Set OLLAMA_MODEL to the model you pulled, or leave as None to auto-detect.
# If the model isn't found, the monitor auto-picks the best available one.
# If Ollama is unreachable, it silently falls back to keyword matching.

USE_OLLAMA    = True
OLLAMA_MODEL  = "llama3"   # ← change to whatever you pulled, or set None for auto
