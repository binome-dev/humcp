"""Twilio tools for sending SMS messages, making voice calls, and checking message status.

Uses the Twilio REST API via the twilio Python package.
See https://www.twilio.com/docs for full documentation.
Requires TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN environment variables.
"""

from __future__ import annotations

import logging
import os
import re

from src.humcp.decorator import tool
from src.tools.messaging.schemas import (
    GetSmsStatusResponse,
    MakeVoiceCallResponse,
    SendSmsResponse,
    SmsSentData,
    SmsStatusData,
    VoiceCallData,
)

try:
    from twilio.base.exceptions import TwilioRestException
    from twilio.rest import Client
except ImportError as err:
    raise ImportError(
        "twilio is required for Twilio tools. Install with: pip install twilio"
    ) from err

logger = logging.getLogger("humcp.tools.twilio")

E164_PATTERN = re.compile(r"^\+[1-9]\d{1,14}$")


def _validate_phone_number(phone: str) -> bool:
    """Validate that a phone number is in E.164 format."""
    return bool(E164_PATTERN.match(phone))


def _get_client() -> tuple[Client | None, str | None]:
    """Create a Twilio client from environment variables.

    Returns:
        Tuple of (client, error_message). If client is None, error_message
        describes what is missing.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    if not account_sid or not auth_token:
        return (
            None,
            "Twilio not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN environment variables.",
        )

    return Client(account_sid, auth_token), None


@tool()
async def twilio_send_sms(
    to: str,
    body: str,
    from_number: str | None = None,
) -> SendSmsResponse:
    """Send an SMS message using Twilio.

    Uses the POST /Messages endpoint of the Twilio REST API.

    Args:
        to: Recipient phone number in E.164 format (e.g., "+1234567890").
        body: The text content of the SMS message (up to 1600 characters).
        from_number: Sender phone number (must be a Twilio number) in E.164 format.
                     Defaults to the TWILIO_FROM_NUMBER environment variable.

    Returns:
        Response indicating success with message SID and status, or an error.
    """
    try:
        client, error = _get_client()
        if client is None:
            return SendSmsResponse(success=False, error=error)

        sender = from_number or os.getenv("TWILIO_FROM_NUMBER")
        if not sender:
            return SendSmsResponse(
                success=False,
                error="No sender number provided. Set TWILIO_FROM_NUMBER or pass from_number parameter.",
            )

        if not _validate_phone_number(to):
            return SendSmsResponse(
                success=False,
                error="'to' number must be in E.164 format (e.g., +1234567890).",
            )
        if not _validate_phone_number(sender):
            return SendSmsResponse(
                success=False,
                error="'from_number' must be in E.164 format (e.g., +1234567890).",
            )

        if not body or not body.strip():
            return SendSmsResponse(
                success=False,
                error="Message body cannot be empty.",
            )

        logger.info("Sending SMS via Twilio to=%s from=%s", to, sender)
        message = client.messages.create(
            to=to,
            from_=sender,
            body=body,
        )

        logger.info("SMS sent successfully sid=%s to=%s", message.sid, to)
        return SendSmsResponse(
            success=True,
            data=SmsSentData(
                message_sid=message.sid,
                to=to,
                from_number=sender,
                status=message.status,
            ),
        )
    except TwilioRestException as e:
        logger.exception("Twilio send_sms failed")
        return SendSmsResponse(success=False, error=f"Twilio API error: {str(e)}")
    except Exception as e:
        logger.exception("Twilio send_sms failed")
        return SendSmsResponse(success=False, error=f"Failed to send SMS: {str(e)}")


@tool()
async def twilio_get_sms_status(message_sid: str) -> GetSmsStatusResponse:
    """Get the delivery status of a Twilio SMS message.

    Uses the GET /Messages/{MessageSid} endpoint. Useful for checking
    whether a message has been delivered, failed, or is still in progress.

    Args:
        message_sid: The SID of the message to check (starts with "SM").

    Returns:
        Response containing the message status and details.
    """
    try:
        client, error = _get_client()
        if client is None:
            return GetSmsStatusResponse(success=False, error=error)

        if not message_sid:
            return GetSmsStatusResponse(success=False, error="message_sid is required.")

        logger.info("Fetching SMS status for sid=%s", message_sid)
        message = client.messages(message_sid).fetch()

        return GetSmsStatusResponse(
            success=True,
            data=SmsStatusData(
                message_sid=message.sid,
                to=message.to,
                from_number=message.from_,
                status=message.status,
                date_sent=str(message.date_sent) if message.date_sent else None,
                error_code=message.error_code,
                error_message=message.error_message,
            ),
        )
    except TwilioRestException as e:
        logger.exception("Twilio get_sms_status failed")
        return GetSmsStatusResponse(success=False, error=f"Twilio API error: {str(e)}")
    except Exception as e:
        logger.exception("Twilio get_sms_status failed")
        return GetSmsStatusResponse(
            success=False, error=f"Failed to get SMS status: {str(e)}"
        )


@tool()
async def twilio_make_call(
    to: str,
    twiml: str,
    from_number: str | None = None,
) -> MakeVoiceCallResponse:
    """Initiate an outbound voice call using Twilio.

    Uses the POST /Calls endpoint of the Twilio REST API. The call behavior
    is controlled by TwiML (Twilio Markup Language) provided in the twiml
    parameter.

    Args:
        to: Recipient phone number in E.164 format (e.g., "+1234567890").
        twiml: TwiML instructions that control the call. For example,
               '<Response><Say>Hello!</Say></Response>' will speak the text
               when the call is answered. See https://www.twilio.com/docs/voice/twiml
               for all available TwiML verbs.
        from_number: Caller ID phone number (must be a Twilio number) in E.164 format.
                     Defaults to the TWILIO_FROM_NUMBER environment variable.

    Returns:
        Response indicating success with call SID and status, or an error.
    """
    try:
        client, error = _get_client()
        if client is None:
            return MakeVoiceCallResponse(success=False, error=error)

        sender = from_number or os.getenv("TWILIO_FROM_NUMBER")
        if not sender:
            return MakeVoiceCallResponse(
                success=False,
                error="No caller ID provided. Set TWILIO_FROM_NUMBER or pass from_number parameter.",
            )

        if not _validate_phone_number(to):
            return MakeVoiceCallResponse(
                success=False,
                error="'to' number must be in E.164 format (e.g., +1234567890).",
            )
        if not _validate_phone_number(sender):
            return MakeVoiceCallResponse(
                success=False,
                error="'from_number' must be in E.164 format (e.g., +1234567890).",
            )

        if not twiml or not twiml.strip():
            return MakeVoiceCallResponse(
                success=False,
                error="twiml cannot be empty. Provide TwiML instructions for the call.",
            )

        logger.info("Making voice call via Twilio to=%s from=%s", to, sender)
        call = client.calls.create(
            to=to,
            from_=sender,
            twiml=twiml,
        )

        logger.info("Voice call initiated sid=%s to=%s", call.sid, to)
        return MakeVoiceCallResponse(
            success=True,
            data=VoiceCallData(
                call_sid=call.sid,
                to=to,
                from_number=sender,
                status=call.status,
            ),
        )
    except TwilioRestException as e:
        logger.exception("Twilio make_call failed")
        return MakeVoiceCallResponse(success=False, error=f"Twilio API error: {str(e)}")
    except Exception as e:
        logger.exception("Twilio make_call failed")
        return MakeVoiceCallResponse(
            success=False, error=f"Failed to make voice call: {str(e)}"
        )
