---
name: social-media
description: Interact with social media platforms including X (Twitter), LinkedIn, and Instagram Business for posting, reading, and monitoring content.
---

# Social Media Tools

Tools for interacting with X (Twitter), LinkedIn, and Instagram Business.

## Requirements

Set environment variables depending on which tools you need:

- **X / Twitter**: `X_BEARER_TOKEN` (read), `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET` (write)
- **LinkedIn**: `LINKEDIN_ACCESS_TOKEN`
- **Instagram Business**: `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_BUSINESS_ACCOUNT_ID`

## X / Twitter

### Post a tweet

```python
result = await x_post_tweet(text="Hello from HuMCP!")
```

### Reply to a tweet

```python
result = await x_reply_to_tweet(
    tweet_id="1234567890",
    text="Great thread!"
)
```

### Read mentions

```python
result = await x_get_mentions(username="myhandle", max_results=20)
```

### Search tweets

```python
result = await x_search_tweets(query="OpenAI", max_results=10)
```

### Get user info

```python
result = await x_get_user(username="elonmusk")
```

### Get user tweets

```python
result = await x_get_user_tweets(username="elonmusk", max_results=10)
```

## LinkedIn

### Get profile

```python
result = await linkedin_get_profile()
```

### Create a post

```python
result = await linkedin_create_share(text="Excited to announce...")
```

## Instagram Business

### Get profile

```python
result = await instagram_get_profile()
```

### Get recent media

```python
result = await instagram_get_recent_media(limit=10)
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
- Posting tweets and replies from automated workflows
- Fetching user profiles and recent timelines
- Creating LinkedIn posts and reading profile data
- Monitoring Instagram Business account media and metrics
