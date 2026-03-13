---
name: messaging-communication
description: Send messages and notifications across messaging platforms including Slack, Discord, Telegram, and WhatsApp. Use when the user needs to send messages, list channels, search messages, or retrieve chat history.
---

# Messaging & Communication Tools

Tools for sending messages and interacting with popular messaging platforms.

## Available Tools

| Tool | Service | Functions |
|------|---------|-----------|
| Slack | Slack | Send messages, list channels, get history, search, reactions, threads |
| Discord | Discord | Send messages, list guild channels, reactions, threads |
| Telegram | Telegram Bot API | Send messages, photos, edit messages, get updates, pin messages |
| WhatsApp | WhatsApp Cloud API | Send text, template, and media messages |

## Requirements

Set environment variables for each service you want to use:

- **Slack**: `SLACK_TOKEN`
- **Discord**: `DISCORD_BOT_TOKEN`
- **Telegram**: `TELEGRAM_BOT_TOKEN`
- **WhatsApp**: `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`

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

### Send a WhatsApp message

```python
result = await whatsapp_send_message(
    to="1234567890",
    message="Your order has been shipped!"
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
- Integrating messaging into multi-step agent pipelines
- Forwarding information between communication platforms
