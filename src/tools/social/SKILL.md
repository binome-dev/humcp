---
name: social-media
description: Interact with X (Twitter) for searching tweets, posting tweets, and fetching user profiles and timelines.
---

# Social Media Tools

Tools for interacting with X (Twitter).

## Requirements

Set environment variables depending on which tools you need:

- **X / Twitter**: `X_BEARER_TOKEN` (read), `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET` (write)

## X / Twitter

### Post a tweet

```python
result = await x_post_tweet(text="Hello from HuMCP!")
```

### Search tweets

```python
result = await x_search_tweets(
    query="OpenAI",
    max_results=10
)
```

### Get user info

```python
result = await x_get_user(username="elonmusk")
```

### Get user tweets

```python
result = await x_get_user_tweets(
    username="elonmusk",
    max_results=10
)
```

## Response Format

All tools return a consistent response:

```json
{
  "success": true,
  "data": { ... }
}
```

On failure:

```json
{
  "success": false,
  "error": "Description of what went wrong"
}
```

## When to Use

- Monitoring X/Twitter for mentions or trending topics
- Posting tweets from automated workflows
- Fetching user profiles and recent timelines
