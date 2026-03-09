---
name: messaging-communication
description: Send messages and notifications across messaging platforms including Slack, Discord, Telegram, WhatsApp, Webex, email (SMTP and Resend), and SMS (Twilio). Use when the user needs to send messages, list channels/rooms, search messages, or retrieve chat history.
---

# Messaging & Communication Tools

Tools for sending messages and interacting with popular messaging platforms and communication services.

## Available Tools

| Tool | Service | Functions |
|------|---------|-----------|
| Slack | Slack | Send messages, list channels, get history, search |
| Discord | Discord | Send messages, list guild channels |
| Telegram | Telegram Bot API | Send messages, get updates |
| Email (SMTP) | Any SMTP server | Send plain-text emails |
| Resend | Resend API | Send HTML emails |
| WhatsApp | WhatsApp Cloud API | Send text messages |
| Webex | Cisco Webex | Send messages, list rooms |
| Twilio | Twilio | Send SMS messages |

## Requirements

Set environment variables for each service you want to use:

- **Slack**: `SLACK_TOKEN`
- **Discord**: `DISCORD_BOT_TOKEN`
- **Telegram**: `TELEGRAM_BOT_TOKEN`
- **Email (SMTP)**: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
- **Resend**: `RESEND_API_KEY`
- **WhatsApp**: `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`
- **Webex**: `WEBEX_ACCESS_TOKEN`
- **Twilio**: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`

## Examples

### Send a Slack message

```python
result = await slack_send_message(
    channel="#general",
    text="Hello from the workflow!"
)
```

### List Slack channels

```python
result = await slack_list_channels()
```

### Search Slack messages

```python
result = await slack_search_messages(
    query="in:#engineering deployment",
    limit=10
)
```

### Send a Discord message

```python
result = await discord_send_message(
    channel_id="1234567890",
    content="Build completed successfully!"
)
```

### Send a Telegram message

```python
result = await telegram_send_message(
    chat_id="@mychannel",
    text="Deployment finished."
)
```

### Send an email via SMTP

```python
result = await send_email(
    to="user@example.com",
    subject="Weekly Report",
    body="Here is your weekly summary..."
)
```

### Send an HTML email via Resend

```python
result = await resend_send_email(
    to="user@example.com",
    subject="Welcome!",
    html="<h1>Welcome aboard</h1><p>We're glad to have you.</p>",
    from_addr="Team <team@yourdomain.com>"
)
```

### Send a WhatsApp message

```python
result = await whatsapp_send_message(
    to="+1234567890",
    message="Your order has been shipped!"
)
```

### Send a Webex message

```python
result = await webex_send_message(
    room_id="Y2lzY29zcGFyazovL...",
    text="Meeting notes posted."
)
```

### Send an SMS via Twilio

```python
result = await twilio_send_sms(
    to="+1234567890",
    body="Your verification code is 123456"
)
```

### Response format

All tools return a consistent response format:

```json
{
  "success": true,
  "data": {
    "message_id": "abc123",
    "channel": "#general",
    "timestamp": "1234567890.123456"
  }
}
```

On error:

```json
{
  "success": false,
  "error": "Slack not configured. Set SLACK_TOKEN environment variable."
}
```

## When to Use

- Sending notifications from automated workflows
- Posting alerts to team channels
- Sending transactional emails or SMS
- Integrating messaging into multi-step agent pipelines
- Forwarding information between communication platforms
