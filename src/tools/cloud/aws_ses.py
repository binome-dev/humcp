"""AWS SES tools for sending emails, managing identities, and viewing statistics.

Wraps Amazon Simple Email Service (SES) via boto3.  Supports sending emails,
listing verified identities, verifying new email addresses, and retrieving
sending statistics.

Environment variables:
    AWS_ACCESS_KEY_ID: AWS access key.
    AWS_SECRET_ACCESS_KEY: AWS secret key.
    AWS_DEFAULT_REGION: Default region (fallback: us-east-1).
    AWS_SES_FROM_EMAIL: Default sender email address.
"""

from __future__ import annotations

import logging
import os

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.cloud.schemas import (
    SesIdentityInfo,
    SesListIdentitiesData,
    SesListIdentitiesResponse,
    SesSendEmailData,
    SesSendEmailResponse,
    SesSendStatisticsData,
    SesSendStatisticsEntry,
    SesSendStatisticsResponse,
    SesVerifyEmailData,
    SesVerifyEmailResponse,
)

try:
    import boto3
except ImportError as err:
    raise ImportError(
        "boto3 is required for AWS SES tools. Install with: pip install boto3"
    ) from err

logger = logging.getLogger("humcp.tools.aws_ses")


def _get_ses_client(aws_key: str, aws_secret: str, region: str | None = None):
    """Create a boto3 SES client with explicit credentials."""
    resolved_region = region or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    return boto3.client(
        "ses",
        region_name=resolved_region,
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret,
    )


@tool()
async def aws_ses_send_email(
    to: str,
    subject: str,
    body: str,
    from_addr: str | None = None,
    html_body: str | None = None,
    cc: str | None = None,
    bcc: str | None = None,
    region: str | None = None,
) -> SesSendEmailResponse:
    """Send an email using AWS Simple Email Service (SES).

    Sends a formatted email to a single recipient with plain text and optional
    HTML body.  The sender address must be verified in SES.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Plain text email body.
        from_addr: Sender email address. Falls back to AWS_SES_FROM_EMAIL env var.
        html_body: Optional HTML version of the email body.
        cc: Optional CC recipient email address.
        bcc: Optional BCC recipient email address.
        region: AWS region. Falls back to AWS_DEFAULT_REGION env var or us-east-1.

    Returns:
        Result with SES message ID on success.
    """
    try:
        aws_key = await resolve_credential("AWS_ACCESS_KEY_ID")
        aws_secret = await resolve_credential("AWS_SECRET_ACCESS_KEY")
        if not aws_key or not aws_secret:
            return SesSendEmailResponse(
                success=False,
                error="AWS credentials not configured. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.",
            )

        resolved_from = from_addr or await resolve_credential("AWS_SES_FROM_EMAIL")
        if not resolved_from:
            return SesSendEmailResponse(
                success=False,
                error="Sender email not configured. Provide from_addr or set AWS_SES_FROM_EMAIL.",
            )

        if not subject:
            return SesSendEmailResponse(
                success=False, error="Email subject cannot be empty."
            )

        if not body:
            return SesSendEmailResponse(
                success=False, error="Email body cannot be empty."
            )

        logger.info("Sending email via SES to=%s subject=%s", to, subject)
        client = _get_ses_client(aws_key, aws_secret, region)

        destination: dict = {"ToAddresses": [to]}
        if cc:
            destination["CcAddresses"] = [cc]
        if bcc:
            destination["BccAddresses"] = [bcc]

        message_body: dict = {
            "Text": {"Charset": "UTF-8", "Data": body},
        }
        if html_body:
            message_body["Html"] = {"Charset": "UTF-8", "Data": html_body}

        response = client.send_email(
            Source=resolved_from,
            Destination=destination,
            Message={
                "Body": message_body,
                "Subject": {"Charset": "UTF-8", "Data": subject},
            },
        )

        message_id = response["MessageId"]
        data = SesSendEmailData(
            message_id=message_id,
            to=to,
            subject=subject,
        )

        logger.info("Email sent successfully message_id=%s", message_id)
        return SesSendEmailResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to send email via SES")
        return SesSendEmailResponse(success=False, error=f"SES email failed: {str(e)}")


@tool()
async def aws_ses_list_identities(
    identity_type: str = "EmailAddress",
    region: str | None = None,
) -> SesListIdentitiesResponse:
    """List verified identities (email addresses or domains) in AWS SES.

    Returns all identities of the specified type that have been submitted
    for verification, regardless of verification status.

    Args:
        identity_type: Type of identity to list. One of 'EmailAddress' (default)
            or 'Domain'.
        region: AWS region. Falls back to AWS_DEFAULT_REGION env var or us-east-1.

    Returns:
        List of identity strings (email addresses or domains).
    """
    try:
        aws_key = await resolve_credential("AWS_ACCESS_KEY_ID")
        aws_secret = await resolve_credential("AWS_SECRET_ACCESS_KEY")
        if not aws_key or not aws_secret:
            return SesListIdentitiesResponse(
                success=False,
                error="AWS credentials not configured. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.",
            )

        valid_types = {"EmailAddress", "Domain"}
        if identity_type not in valid_types:
            return SesListIdentitiesResponse(
                success=False,
                error=f"Invalid identity_type '{identity_type}'. Must be one of: {', '.join(sorted(valid_types))}",
            )

        logger.info("Listing SES identities type=%s", identity_type)
        client = _get_ses_client(aws_key, aws_secret, region)
        response = client.list_identities(IdentityType=identity_type, MaxItems=100)

        identities = [
            SesIdentityInfo(identity=ident, identity_type=identity_type)
            for ident in response.get("Identities", [])
        ]

        data = SesListIdentitiesData(
            identities=identities,
            count=len(identities),
        )

        logger.info("Listed %d SES identities", len(identities))
        return SesListIdentitiesResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to list SES identities")
        return SesListIdentitiesResponse(
            success=False, error=f"Failed to list SES identities: {str(e)}"
        )


@tool()
async def aws_ses_get_send_statistics(
    region: str | None = None,
) -> SesSendStatisticsResponse:
    """Get sending statistics for AWS SES.

    Returns a list of data points representing the last two weeks of sending
    activity, including delivery attempts, bounces, complaints, and rejects.

    Args:
        region: AWS region. Falls back to AWS_DEFAULT_REGION env var or us-east-1.

    Returns:
        List of send statistics data points.
    """
    try:
        aws_key = await resolve_credential("AWS_ACCESS_KEY_ID")
        aws_secret = await resolve_credential("AWS_SECRET_ACCESS_KEY")
        if not aws_key or not aws_secret:
            return SesSendStatisticsResponse(
                success=False,
                error="AWS credentials not configured. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.",
            )

        logger.info("Getting SES send statistics")
        client = _get_ses_client(aws_key, aws_secret, region)
        response = client.get_send_statistics()

        statistics = [
            SesSendStatisticsEntry(
                timestamp=str(dp.get("Timestamp", "")) if dp.get("Timestamp") else None,
                delivery_attempts=dp.get("DeliveryAttempts", 0),
                bounces=dp.get("Bounces", 0),
                complaints=dp.get("Complaints", 0),
                rejects=dp.get("Rejects", 0),
            )
            for dp in response.get("SendDataPoints", [])
        ]

        data = SesSendStatisticsData(
            statistics=statistics,
            count=len(statistics),
        )

        logger.info("Got %d SES statistics data points", len(statistics))
        return SesSendStatisticsResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to get SES send statistics")
        return SesSendStatisticsResponse(
            success=False, error=f"Failed to get send statistics: {str(e)}"
        )


@tool()
async def aws_ses_verify_email(
    email: str,
    region: str | None = None,
) -> SesVerifyEmailResponse:
    """Send a verification email to an address for use with AWS SES.

    Amazon SES sends a verification email to the specified address.  The
    recipient must click the link in the email to complete verification
    before the address can be used as a sender.

    Args:
        email: The email address to verify.
        region: AWS region. Falls back to AWS_DEFAULT_REGION env var or us-east-1.

    Returns:
        Confirmation that the verification email was sent.
    """
    try:
        aws_key = await resolve_credential("AWS_ACCESS_KEY_ID")
        aws_secret = await resolve_credential("AWS_SECRET_ACCESS_KEY")
        if not aws_key or not aws_secret:
            return SesVerifyEmailResponse(
                success=False,
                error="AWS credentials not configured. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.",
            )

        if not email:
            return SesVerifyEmailResponse(
                success=False, error="Email address cannot be empty."
            )

        logger.info("Sending SES verification email to=%s", email)
        client = _get_ses_client(aws_key, aws_secret, region)
        client.verify_email_identity(EmailAddress=email)

        data = SesVerifyEmailData(
            email=email,
            message=f"Verification email sent to {email}. Check inbox and click the verification link.",
        )

        logger.info("SES verification email sent to=%s", email)
        return SesVerifyEmailResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to send SES verification email")
        return SesVerifyEmailResponse(
            success=False, error=f"Failed to verify email: {str(e)}"
        )
