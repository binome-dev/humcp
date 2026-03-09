"""Resend email tools for sending emails via the Resend API.

Supports single and batch email sending, and retrieving sent email details.
See https://resend.com/docs/api-reference for full API documentation.
Requires the RESEND_API_KEY environment variable.
"""

from __future__ import annotations

import logging
import os

from src.humcp.decorator import tool
from src.tools.messaging.schemas import (
    BatchEmailResultItem,
    BatchEmailSentData,
    BatchEmailSentResponse,
    EmailSentData,
    SendEmailResponse,
)

try:
    import resend as resend_lib
except ImportError as err:
    raise ImportError(
        "resend is required for Resend tools. Install with: pip install resend"
    ) from err

logger = logging.getLogger("humcp.tools.resend")


def _configure_api_key() -> str | None:
    """Set the Resend API key from environment and return it."""
    api_key = os.getenv("RESEND_API_KEY")
    if api_key:
        resend_lib.api_key = api_key
    return api_key


@tool()
async def resend_send_email(
    to: str,
    subject: str,
    html: str,
    from_addr: str | None = None,
    text: str | None = None,
    cc: str | None = None,
    bcc: str | None = None,
    reply_to: str | None = None,
) -> SendEmailResponse:
    """Send an email using the Resend API.

    Uses the POST /emails endpoint. Resend requires a verified sender domain.

    Args:
        to: Recipient email address. For multiple recipients, separate with commas.
        subject: Email subject line.
        html: HTML body of the email.
        from_addr: Sender email address (e.g., "Name <name@domain.com>").
                   Required by Resend; must use a verified domain.
        text: Optional plain-text body (fallback for email clients that
              do not render HTML).
        cc: CC recipients, separated by commas.
        bcc: BCC recipients, separated by commas.
        reply_to: Reply-to email address.

    Returns:
        Response indicating success with email ID and details, or an error.
    """
    try:
        if not _configure_api_key():
            return SendEmailResponse(
                success=False,
                error="Resend not configured. Set RESEND_API_KEY environment variable.",
            )

        if not from_addr:
            return SendEmailResponse(
                success=False,
                error="from_addr is required for Resend emails. Provide a verified sender address.",
            )

        to_list = [addr.strip() for addr in to.split(",")]

        logger.info("Sending email via Resend to=%s subject=%s", to, subject)

        params: dict = {
            "from": from_addr,
            "to": to_list,
            "subject": subject,
            "html": html,
        }
        if text:
            params["text"] = text
        if cc:
            params["cc"] = [addr.strip() for addr in cc.split(",")]
        if bcc:
            params["bcc"] = [addr.strip() for addr in bcc.split(",")]
        if reply_to:
            params["reply_to"] = reply_to

        result = resend_lib.Emails.send(params)

        message_id = None
        if isinstance(result, dict):
            message_id = result.get("id")

        logger.info("Resend email sent successfully to=%s", to)
        return SendEmailResponse(
            success=True,
            data=EmailSentData(
                message_id=message_id,
                to=to,
                subject=subject,
            ),
        )
    except Exception as e:
        logger.exception("Resend send_email failed")
        return SendEmailResponse(
            success=False, error=f"Failed to send email via Resend: {str(e)}"
        )


@tool()
async def resend_send_batch_emails(
    from_addr: str,
    to_addresses: str,
    subject: str,
    html: str,
) -> BatchEmailSentResponse:
    """Send a batch of emails using the Resend batch API.

    Uses the POST /emails/batch endpoint. Sends the same content to multiple
    recipients as individual emails (up to 100 per call). Each recipient
    receives their own email and cannot see other recipients.

    Args:
        from_addr: Sender email address (must use a verified domain).
        to_addresses: Comma-separated list of recipient email addresses (max 100).
        subject: Email subject line (same for all recipients).
        html: HTML body of the email (same for all recipients).

    Returns:
        Response indicating success with individual email IDs, or an error.
    """
    try:
        if not _configure_api_key():
            return BatchEmailSentResponse(
                success=False,
                error="Resend not configured. Set RESEND_API_KEY environment variable.",
            )

        recipients = [addr.strip() for addr in to_addresses.split(",") if addr.strip()]
        if not recipients:
            return BatchEmailSentResponse(
                success=False,
                error="No valid recipient addresses provided.",
            )
        if len(recipients) > 100:
            return BatchEmailSentResponse(
                success=False,
                error="Resend batch API supports a maximum of 100 recipients per call.",
            )

        logger.info("Sending batch email via Resend to %d recipients", len(recipients))

        batch_params = [
            {
                "from": from_addr,
                "to": [recipient],
                "subject": subject,
                "html": html,
            }
            for recipient in recipients
        ]

        result = resend_lib.Batch.send(batch_params)

        items: list[BatchEmailResultItem] = []
        if isinstance(result, dict):
            for item in result.get("data", []):
                items.append(BatchEmailResultItem(id=item.get("id")))
        elif isinstance(result, list):
            for item in result:
                item_id = item.get("id") if isinstance(item, dict) else None
                items.append(BatchEmailResultItem(id=item_id))

        logger.info("Batch email sent successfully, %d emails", len(items))
        return BatchEmailSentResponse(
            success=True,
            data=BatchEmailSentData(results=items, count=len(items)),
        )
    except Exception as e:
        logger.exception("Resend send_batch_emails failed")
        return BatchEmailSentResponse(
            success=False, error=f"Failed to send batch emails via Resend: {str(e)}"
        )
