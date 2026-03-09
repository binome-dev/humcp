---
name: social-media
description: Interact with social media platforms including Reddit, X (Twitter), Hacker News, and YouTube. Use for searching posts/tweets, fetching content, browsing top stories, or retrieving video information and captions.
---

# Social Media Tools

Tools for interacting with Reddit, X (Twitter), Hacker News, and YouTube.

## Requirements

Set environment variables depending on which tools you need:

- **Reddit**: `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT` (optional)
- **X / Twitter**: `X_BEARER_TOKEN` (read), `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET` (write)
- **YouTube**: `YOUTUBE_API_KEY`
- **Hacker News**: No API key required

## Reddit

### Search posts

```python
result = await reddit_search_posts(
    query="machine learning",
    subreddit="python",
    limit=10
)
```

### Get a specific post

```python
result = await reddit_get_post(post_id="1abc23d")
```

### Get top posts

```python
result = await reddit_get_top_posts(
    subreddit="programming",
    time_filter="week",
    limit=10
)
```

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

## Hacker News

### Get top stories

```python
result = await hackernews_get_top_stories(limit=10)
```

### Get a specific story

```python
result = await hackernews_get_story(story_id=12345678)
```

### Search stories

```python
result = await hackernews_search(query="Rust programming", limit=10)
```

## YouTube

### Search videos

```python
result = await youtube_search(query="Python tutorial", max_results=5)
```

### Get video info

```python
result = await youtube_get_video_info(video_id="dQw4w9WgXcQ")
```

### Get video captions

```python
result = await youtube_get_captions(video_id="dQw4w9WgXcQ")
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

- Searching Reddit for community discussions or opinions
- Monitoring X/Twitter for mentions or trending topics
- Browsing Hacker News for tech news and discussions
- Searching YouTube for videos or retrieving video transcripts
