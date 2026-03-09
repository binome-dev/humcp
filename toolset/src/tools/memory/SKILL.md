---
name: persistent-memory
description: Store, search, and retrieve persistent memories and conversation history using Mem0 or Zep. Use when the user needs to remember facts, maintain context across sessions, or manage conversational memory.
---

# Memory Tools

Tools for persistent memory storage and retrieval across conversations.

## Mem0 Tools

Store and search user memories with semantic search via Mem0.

### Requirements

Set environment variable:
- `MEM0_API_KEY`: Your Mem0 API key

### Store a Memory

```python
result = await mem0_add_memory(
    content="User prefers Python for data analysis",
    user_id="user-123",
    metadata={"category": "preferences"}
)
```

### Search Memories

```python
result = await mem0_search_memory(
    query="programming preferences",
    user_id="user-123",
    limit=5
)
```

### Get All Memories

```python
result = await mem0_get_memories(user_id="user-123")
```

## Zep Tools

Session-based conversation memory with knowledge graph extraction.

### Requirements

Set environment variables:
- `ZEP_API_KEY`: Your Zep API key

### Add Message to Session

```python
result = await zep_add_memory(
    session_id="session-abc",
    content="I work at Acme Corp as a data scientist",
    role="user"
)
```

### Search Session Memory

```python
result = await zep_search_memory(
    session_id="session-abc",
    query="work information",
    limit=5
)
```

### Get Session Context

```python
result = await zep_get_session(session_id="session-abc")
```

### Response Format

All tools return:

```json
{
  "success": true,
  "data": { ... }
}
```

## When to Use

- Storing user preferences and facts for personalization
- Maintaining context across multiple conversation sessions
- Building knowledge graphs from conversation history
- Semantic search over previously stored information
- Retrieving session summaries and context
