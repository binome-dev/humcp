---
name: http-api-client
description: Make HTTP requests to any URL or API endpoint. Use when the user needs to call a REST API, fetch data from a URL, send webhooks, or test HTTP endpoints. Supports GET, POST, PUT, PATCH, DELETE methods with custom headers and JSON body.
---

# HTTP API Client Tools

General-purpose HTTP client for making requests to any URL or API endpoint.

## Available Tools

| Tool | API Key Required | Best For |
|------|-----------------|----------|
| `http_request` | None | Making HTTP requests to any URL |

## Quick Examples

### GET request

```python
result = await http_request(
    method="GET",
    url="https://api.example.com/users",
    headers={"Authorization": "Bearer token123"}
)
```

### POST request with JSON body

```python
result = await http_request(
    method="POST",
    url="https://api.example.com/users",
    headers={"Content-Type": "application/json"},
    body={"name": "Alice", "email": "alice@example.com"},
    timeout=15
)
```

### PUT request

```python
result = await http_request(
    method="PUT",
    url="https://api.example.com/users/123",
    body={"name": "Alice Updated"}
)
```

### DELETE request

```python
result = await http_request(
    method="DELETE",
    url="https://api.example.com/users/123"
)
```

## Response Format

```json
{
  "success": true,
  "data": {
    "status_code": 200,
    "headers": {"content-type": "application/json"},
    "body": {"id": 1, "name": "Alice"},
    "url": "https://api.example.com/users",
    "method": "GET",
    "elapsed_ms": 152.34
  }
}
```

On failure:

```json
{
  "success": false,
  "error": "Connection failed: ..."
}
```

## When to Use

- **Call REST APIs**: Make GET/POST/PUT/PATCH/DELETE requests
- **Fetch data**: Retrieve JSON or text from any URL
- **Send webhooks**: POST data to webhook endpoints
- **Test endpoints**: Verify API responses and status codes
- **Integration glue**: Connect to any HTTP-based service
