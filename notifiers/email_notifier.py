"""
Email notifications via Gmail SMTP (free).
Setup: enable 2-FA on your Google account, then create an App Password at
https://myaccount.google.com/apppasswords  — use that as GMAIL_APP_PASSWORD.
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

logger = logging.getLogger(__name__)


def _build_html(jobs: list[dict]) -> str:
    rows = ""
    for j in jobs:
        rows += f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #eee;">
            <strong>{j['company']}</strong>
          </td>
          <td style="padding:10px;border-bottom:1px solid #eee;">{j['title']}</td>
          <td style="padding:10px;border-bottom:1px solid #eee;">
            <a href="{j['url']}" style="color:#2563eb;font-weight:600;">Apply →</a>
          </td>
        </tr>"""

    return f"""
    <html><body style="font-family:sans-serif;color:#111;max-width:640px;margin:auto;">
      <h2 style="color:#1e40af;">🤖 New DS/ML/AI Job Alerts</h2>
      <p style="color:#555;">{datetime.now().strftime('%B %d, %Y %I:%M %p')}</p>
      <table width="100%" style="border-collapse:collapse;margin-top:16px;">
        <thead>
          <tr style="background:#f1f5f9;">
            <th style="padding:10px;text-align:left;">Company</th>
            <th style="padding:10px;text-align:left;">Role</th>
            <th style="padding:10px;text-align:left;">Link</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
      <p style="color:#9ca3af;font-size:12px;margin-top:24px;">
        Sent by Job Monitor · running locally on your machine
      </p>
    </body></html>"""


def _build_plain(jobs: list[dict]) -> str:
    lines = [f"New DS/ML/AI Jobs — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"]
    for j in jobs:
        lines.append(f"• [{j['company']}] {j['title']}")
        lines.append(f"  {j['url']}\n")
    return "\n".join(lines)


def send_email(
    jobs: list[dict],
    sender_email: str,
    app_password: str,
    recipient_email: str,
) -> bool:
    if not jobs:
        return True

    subject = f"🚀 {len(jobs)} New Job Alert{'s' if len(jobs)>1 else ''} — DS/ML/AI"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg.attach(MIMEText(_build_plain(jobs), "plain"))
    msg.attach(MIMEText(_build_html(jobs), "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        logger.info(f"Email sent to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Email failed: {e}")
        return False
