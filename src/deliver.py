"""Deliver the finished draft to the editor: e-mail (SMTP) and/or Telegram."""

import os
import smtplib
import urllib.request
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(subject: str, markdown_body: str) -> bool:
    """Send the draft via SMTP. Uses Gmail-style app-password auth.

    Required env vars: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EDITOR_EMAIL
    """
    host = os.environ.get("SMTP_HOST")
    user = os.environ.get("SMTP_USER")
    if not host or not user:
        print("  [skip] SMTP nije konfiguriran (SMTP_HOST/SMTP_USER).")
        return False

    port = int(os.environ.get("SMTP_PORT", "587"))
    password = os.environ["SMTP_PASS"]
    to_addr = os.environ.get("EDITOR_EMAIL", user)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_addr
    msg.attach(MIMEText(markdown_body, "plain", "utf-8"))

    try:
        import markdown as md  # optional dependency

        html_body = f"<div style='font-family:Georgia,serif;max-width:640px'>{md.markdown(markdown_body)}</div>"
        msg.attach(MIMEText(html_body, "html", "utf-8"))
    except ImportError:
        pass

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(user, [to_addr], msg.as_string())
    print(f"  [OK] Draft poslan na {to_addr}")
    return True


def notify_telegram(text: str) -> bool:
    """Short Telegram ping so the editor knows the draft is ready.

    Required env vars: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text[:4000]}).encode()
    try:
        urllib.request.urlopen(url, data=data, timeout=15)
        print("  [OK] Telegram obavijest poslana")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"  [FAIL] Telegram: {e}")
        return False
