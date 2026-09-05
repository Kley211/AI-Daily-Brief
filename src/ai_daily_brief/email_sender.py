"""SMTP delivery for rendered daily digests."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

from .digest import DigestReport, render_html, render_text


def send_report(report: DigestReport, recipient: str | None = None) -> str:
    host = os.getenv("AI_BRIEF_SMTP_HOST", "")
    if not host:
        raise RuntimeError("AI_BRIEF_SMTP_HOST is required to send email")
    target = recipient or os.getenv("AI_BRIEF_RECIPIENT", "")
    if not target:
        raise RuntimeError("AI_BRIEF_RECIPIENT is required to send email")
    port = int(os.getenv("AI_BRIEF_SMTP_PORT", "587"))
    username = os.getenv("AI_BRIEF_SMTP_USERNAME", "")
    password = os.getenv("AI_BRIEF_SMTP_PASSWORD", "")
    sender = os.getenv("AI_BRIEF_SMTP_FROM", username or target)
    message = EmailMessage()
    message["Subject"] = f"AI Daily Brief | {report.digest_date.isoformat()}"
    message["From"] = sender
    message["To"] = target
    message.set_content(render_text(report))
    message.add_alternative(render_html(report), subtype="html")
    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.starttls()
        if username:
            smtp.login(username, password)
        smtp.send_message(message)
    return target
