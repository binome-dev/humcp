"""SMTP email tool for sending emails via a configured SMTP server.

Supports plain-text and HTML emails, CC/BCC recipients, and
auto-negotiation of TLS (STARTTLS on port 587, implicit SSL on port 465).
Requires SMTP_HOST, SMTP_USERNAME, and SMTP_PASSWORD environment variables.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.messaging.schemas import (
    EmailSentData,
    SendEmailResponse,
)

logger = logging.getLogger("humcp.tools.email_smtp")


@tool()
async def send_email(
    to: str,
    subject: str,
    body: str,
    from_addr: str | None = None,
    html_body: str | None = None,
    cc: str | None = None,
    bcc: str | None = None,
) -> SendEmailResponse:
    """Send an email via SMTP.

    Connects to the SMTP server configured through environment variables.
    Uses STARTTLS on port 587 (default) or implicit SSL on port 465.

    Args:
        to: Recipient email address. Multiple recipients can be separated by commas.
        subject: Email subject line.
        body: Plain-text email body. Used as fallback when html_body is also provided.
        from_addr: Sender email address. Defaults to the SMTP_USERNAME env var.
        html_body: Optional HTML body. When provided, the email is sent as
                   multipart/alternative with both plain-text and HTML parts.
        cc: CC recipients, separated by commas. Visible to all recipients.
        bcc: BCC recipients, separated by commas. Hidden from other recipients.

    Returns:
        Response indicating success with email details, or an error.
    """
    try:
        smtp_host = await resolve_credential("SMTP_HOST")
        smtp_port_str = await resolve_credential("SMTP_PORT") or "587"
        smtp_username = await resolve_credential("SMTP_USERNAME")
        smtp_password = await resolve_credential("SMTP_PASSWORD")

        if not smtp_host:
            return SendEmailResponse(
                success=False,
                error="SMTP not configured. Set SMTP_HOST environment variable.",
            )
        if not smtp_username or not smtp_password:
            return SendEmailResponse(
                success=False,
                error="SMTP credentials not configured. Set SMTP_USERNAME and SMTP_PASSWORD environment variables.",
            )

        try:
            smtp_port = int(smtp_port_str)
        except ValueError:
            return SendEmailResponse(
                success=False,
                error=f"Invalid SMTP_PORT value: {smtp_port_str}",
            )

        sender = from_addr or smtp_username

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = to

        if cc:
            msg["Cc"] = cc
        if bcc:
            msg["Bcc"] = bcc

        msg.set_content(body)

        if html_body:
            msg.add_alternative(html_body, subtype="html")

        # Build the full recipient list for the SMTP envelope
        all_recipients = [addr.strip() for addr in to.split(",")]
        if cc:
            all_recipients.extend(addr.strip() for addr in cc.split(","))
        if bcc:
            all_recipients.extend(addr.strip() for addr in bcc.split(","))

        logger.info(
            "Sending email to=%s subject=%s via %s:%d",
            to,
            subject,
            smtp_host,
            smtp_port,
        )

        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)

        logger.info("Email sent successfully to=%s", to)
        return SendEmailResponse(
            success=True,
            data=EmailSentData(
                to=to,
                subject=subject,
            ),
        )
    except smtplib.SMTPAuthenticationError as e:
        logger.exception("SMTP authentication failed")
        return SendEmailResponse(
            success=False, error=f"SMTP authentication failed: {str(e)}"
        )
    except smtplib.SMTPException as e:
        logger.exception("SMTP error sending email")
        return SendEmailResponse(success=False, error=f"SMTP error: {str(e)}")
    except Exception as e:
        logger.exception("Failed to send email")
        return SendEmailResponse(success=False, error=f"Failed to send email: {str(e)}")
