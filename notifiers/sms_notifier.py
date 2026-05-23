"""
Free SMS notifications via carrier email-to-SMS gateways.
No Twilio, no cost. Just send an email to <number>@<carrier-gateway>.

Supported carriers (US):
  AT&T        → number@txt.att.net
  T-Mobile    → number@tmomail.net
  Verizon     → number@vtext.com
  Sprint      → number@messaging.sprintpcs.com
  Boost       → number@sms.myboostmobile.com
  Cricket     → number@sms.cricketwireless.net
  Metro PCS   → number@mymetropcs.com
  US Cellular → number@email.uscc.net
  Google Fi   → number@msg.fi.google.com

International carriers: many have similar gateways — Google "<carrier> email to SMS gateway".
"""

import smtplib
import logging
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

CARRIER_GATEWAYS = {
    "att": "txt.att.net",
    "tmobile": "tmomail.net",
    "t-mobile": "tmomail.net",
    "verizon": "vtext.com",
    "sprint": "messaging.sprintpcs.com",
    "boost": "sms.myboostmobile.com",
    "cricket": "sms.cricketwireless.net",
    "metro": "mymetropcs.com",
    "uscellular": "email.uscc.net",
    "fi": "msg.fi.google.com",
    "googlefi": "msg.fi.google.com",
}


def get_sms_address(phone_number: str, carrier: str) -> str:
    """
    phone_number: 10-digit US number, e.g. '5551234567'
    carrier: one of the keys in CARRIER_GATEWAYS
    """
    digits = "".join(filter(str.isdigit, phone_number))
    gateway = CARRIER_GATEWAYS.get(carrier.lower().replace(" ", ""))
    if not gateway:
        raise ValueError(
            f"Unknown carrier '{carrier}'. "
            f"Valid options: {', '.join(CARRIER_GATEWAYS.keys())}"
        )
    return f"{digits}@{gateway}"


def send_sms(
    jobs: list[dict],
    sender_email: str,
    app_password: str,
    phone_number: str,
    carrier: str,
) -> bool:
    if not jobs:
        return True

    sms_address = get_sms_address(phone_number, carrier)

    # SMS must be short — carriers drop long messages
    lines = [f"Job Alert: {len(jobs)} new DS/ML/AI role(s)\n"]
    for j in jobs[:3]:  # cap at 3 to stay within SMS size limits
        lines.append(f"{j['company']}: {j['title'][:40]}")
        lines.append(j["url"][:60])
    if len(jobs) > 3:
        lines.append(f"...and {len(jobs)-3} more. Check your email.")

    body = "\n".join(lines)

    msg = MIMEText(body)
    msg["From"] = sender_email
    msg["To"] = sms_address

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, sms_address, msg.as_string())
        logger.info(f"SMS sent to {sms_address}")
        return True
    except Exception as e:
        logger.error(f"SMS failed: {e}")
        return False
