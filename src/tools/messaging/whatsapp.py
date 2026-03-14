"""WhatsApp Cloud API tools for sending text, template, and media messages.

Uses the Meta WhatsApp Business Cloud API (https://developers.facebook.com/docs/whatsapp/cloud-api).
Requires WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID environment variables.
"""

from __future__ import annotations

import logging
import os

from src.humcp.decorator import tool
from src.tools.messaging.schemas import (
    MessageSentData,
    SendMessageResponse,
    SendWhatsAppMediaResponse,
    SendWhatsAppTemplateResponse,
    WhatsAppInboundMessage,
    WhatsAppMediaSentData,
    WhatsAppTemplateSentData,
    WhatsAppWebhookData,
    WhatsAppWebhookResponse,
)

try:
    import httpx
except ImportError as err:
    raise ImportError(
        "httpx is required for WhatsApp tools. Install with: pip install httpx"
    ) from err

logger = logging.getLogger("humcp.tools.whatsapp")

WHATSAPP_API_BASE = "https://graph.facebook.com"
WHATSAPP_API_VERSION = "v22.0"


def _get_config() -> tuple[str, str, dict[str, str]] | None:
    """Get WhatsApp API configuration from environment.

    Returns:
        Tuple of (url, phone_number_id, headers) or None if not configured.
    """
    token = os.getenv("WHATSAPP_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    if not token or not phone_number_id:
        return None

    url = f"{WHATSAPP_API_BASE}/{WHATSAPP_API_VERSION}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    return url, phone_number_id, headers


@tool()
async def whatsapp_send_message(
    to: str, message: str, preview_url: bool = False
) -> SendMessageResponse:
    """Send a text message via the WhatsApp Cloud API.

    Uses the POST /{phone_number_id}/messages endpoint. The recipient must
    have an active WhatsApp account on the given phone number.

    Args:
        to: Recipient's phone number in international format without the leading
            '+' sign (e.g., "1234567890" for a US number). Must include country code.
        message: The text message to send (up to 4096 characters).
        preview_url: If true, WhatsApp will attempt to render a link preview
                     for the first URL found in the message text.

    Returns:
        Response indicating success with message ID, or an error.
    """
    try:
        config = _get_config()
        if config is None:
            return SendMessageResponse(
                success=False,
                error="WhatsApp not configured. Set WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID environment variables.",
            )

        url, _, headers = config
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": preview_url, "body": message},
        }

        logger.info("Sending WhatsApp message to=%s", to)
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

        messages_list = data.get("messages", [])
        message_id = messages_list[0].get("id") if messages_list else None

        logger.info("WhatsApp message sent successfully to=%s", to)
        return SendMessageResponse(
            success=True,
            data=MessageSentData(
                message_id=message_id,
                channel=to,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("WhatsApp send_message HTTP error")
        return SendMessageResponse(
            success=False,
            error=f"WhatsApp API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("WhatsApp send_message failed")
        return SendMessageResponse(
            success=False, error=f"Failed to send WhatsApp message: {str(e)}"
        )


@tool()
async def whatsapp_send_template(
    to: str,
    template_name: str,
    language_code: str = "en_US",
    header_params: str | None = None,
    body_params: str | None = None,
) -> SendWhatsAppTemplateResponse:
    """Send a pre-approved template message via the WhatsApp Cloud API.

    Uses the POST /{phone_number_id}/messages endpoint with type "template".
    Templates must be created and approved in the Meta Business Manager before
    they can be used. Template messages are required to initiate conversations
    outside the 24-hour customer service window.

    Args:
        to: Recipient's phone number in international format without the leading
            '+' sign (e.g., "1234567890"). Must include country code.
        template_name: The name of the approved message template.
        language_code: The language/locale code for the template (default "en_US").
                       Must match a language the template was approved for.
        header_params: Optional comma-separated parameter values for the template
                       header (e.g., "John Doe" or "Order #123").
        body_params: Optional comma-separated parameter values for the template
                     body placeholders (e.g., "John,42,shipped").

    Returns:
        Response indicating success with message ID, or an error.
    """
    try:
        config = _get_config()
        if config is None:
            return SendWhatsAppTemplateResponse(
                success=False,
                error="WhatsApp not configured. Set WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID environment variables.",
            )

        url, _, headers = config

        template: dict = {
            "name": template_name,
            "language": {"code": language_code},
        }

        components: list[dict] = []
        if header_params:
            params = [
                {"type": "text", "text": p.strip()} for p in header_params.split(",")
            ]
            components.append({"type": "header", "parameters": params})

        if body_params:
            params = [
                {"type": "text", "text": p.strip()} for p in body_params.split(",")
            ]
            components.append({"type": "body", "parameters": params})

        if components:
            template["components"] = components

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": template,
        }

        logger.info(
            "Sending WhatsApp template=%s to=%s lang=%s",
            template_name,
            to,
            language_code,
        )
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

        messages_list = data.get("messages", [])
        message_id = messages_list[0].get("id") if messages_list else None

        logger.info("WhatsApp template sent successfully to=%s", to)
        return SendWhatsAppTemplateResponse(
            success=True,
            data=WhatsAppTemplateSentData(
                message_id=message_id,
                to=to,
                template_name=template_name,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("WhatsApp send_template HTTP error")
        return SendWhatsAppTemplateResponse(
            success=False,
            error=f"WhatsApp API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("WhatsApp send_template failed")
        return SendWhatsAppTemplateResponse(
            success=False, error=f"Failed to send WhatsApp template: {str(e)}"
        )


@tool()
async def whatsapp_send_media(
    to: str,
    media_type: str,
    media_url: str,
    caption: str | None = None,
    filename: str | None = None,
) -> SendWhatsAppMediaResponse:
    """Send a media message (image, document, video, or audio) via WhatsApp.

    Uses the POST /{phone_number_id}/messages endpoint with the specified
    media type. The media must be accessible via a public URL.

    Args:
        to: Recipient's phone number in international format without the leading
            '+' sign (e.g., "1234567890"). Must include country code.
        media_type: Type of media to send. Must be one of: "image", "document",
                    "video", "audio". Images support JPEG/PNG (max 5 MB),
                    documents support PDF/DOC/etc. (max 100 MB), videos support
                    MP4 (max 16 MB), audio supports MP3/OGG (max 16 MB).
        media_url: Public URL of the media file to send.
        caption: Optional caption for the media (supported for image, video,
                 and document types; up to 1024 characters).
        filename: Optional filename for documents (shown to the recipient).

    Returns:
        Response indicating success with message ID, or an error.
    """
    try:
        config = _get_config()
        if config is None:
            return SendWhatsAppMediaResponse(
                success=False,
                error="WhatsApp not configured. Set WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID environment variables.",
            )

        valid_types = {"image", "document", "video", "audio"}
        if media_type not in valid_types:
            return SendWhatsAppMediaResponse(
                success=False,
                error=f"Invalid media_type '{media_type}'. Must be one of: {', '.join(sorted(valid_types))}.",
            )

        url, _, headers = config

        media_payload: dict = {"link": media_url}
        if caption and media_type in {"image", "video", "document"}:
            media_payload["caption"] = caption
        if filename and media_type == "document":
            media_payload["filename"] = filename

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": media_type,
            media_type: media_payload,
        }

        logger.info("Sending WhatsApp %s to=%s url=%s", media_type, to, media_url)
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()

        messages_list = data.get("messages", [])
        message_id = messages_list[0].get("id") if messages_list else None

        logger.info("WhatsApp %s sent successfully to=%s", media_type, to)
        return SendWhatsAppMediaResponse(
            success=True,
            data=WhatsAppMediaSentData(
                message_id=message_id,
                to=to,
                media_type=media_type,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("WhatsApp send_media HTTP error")
        return SendWhatsAppMediaResponse(
            success=False,
            error=f"WhatsApp API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("WhatsApp send_media failed")
        return SendWhatsAppMediaResponse(
            success=False, error=f"Failed to send WhatsApp media: {str(e)}"
        )


@tool()
async def whatsapp_parse_webhook(payload: str) -> WhatsAppWebhookResponse:
    """Parse an inbound WhatsApp Cloud API webhook payload to extract messages.

    Processes the JSON payload sent by the WhatsApp Cloud API webhook
    (Webhooks → messages notification). Extracts inbound text messages and
    delivery status updates from the payload.

    This tool is intended to be called from a workflow that receives webhook
    events, passing the raw JSON body as a string.

    Args:
        payload: The raw JSON string of the webhook payload from the
                 WhatsApp Cloud API.

    Returns:
        Parsed inbound messages and delivery status updates.
    """
    import json

    try:
        data = json.loads(payload)
    except (json.JSONDecodeError, TypeError) as e:
        return WhatsAppWebhookResponse(
            success=False,
            error=f"Invalid JSON payload: {e}",
        )

    try:
        messages: list[WhatsAppInboundMessage] = []
        statuses: list[dict] = []

        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})

                # Extract inbound messages
                for msg in value.get("messages", []):
                    text_body = None
                    if msg.get("type") == "text":
                        text_body = msg.get("text", {}).get("body")

                    messages.append(
                        WhatsAppInboundMessage(
                            message_id=msg.get("id", ""),
                            from_number=msg.get("from", ""),
                            timestamp=msg.get("timestamp", ""),
                            type=msg.get("type", "text"),
                            text=text_body,
                        )
                    )

                # Extract delivery status updates
                for status in value.get("statuses", []):
                    statuses.append(
                        {
                            "id": status.get("id"),
                            "status": status.get("status"),
                            "timestamp": status.get("timestamp"),
                            "recipient_id": status.get("recipient_id"),
                        }
                    )

        logger.info(
            "WhatsApp webhook parsed messages=%d statuses=%d",
            len(messages),
            len(statuses),
        )
        return WhatsAppWebhookResponse(
            success=True,
            data=WhatsAppWebhookData(
                messages=messages,
                count=len(messages),
                statuses=statuses,
            ),
        )
    except Exception as e:
        logger.exception("WhatsApp webhook parsing failed")
        return WhatsAppWebhookResponse(
            success=False, error=f"Failed to parse WhatsApp webhook: {str(e)}"
        )
