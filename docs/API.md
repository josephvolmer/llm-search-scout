# API Documentation

## Overview

The LLM Search API provides two main endpoints for searching the web with LLM-optimized results.

Base URL: `http://localhost:8000/api/v1`

## Authentication

All endpoints require an API key passed via the `X-API-Key` header.

```http
X-API-Key: your-api-key-here
```

**Response Codes:**
- `401 Unauthorized`: Missing API key
- `403 Forbidden`: Invalid API key
- `429 Too Many Requests`: Rate limit exceeded

## Endpoints

### Health Check

Check if the API is running and can connect to SearXNG.

```http
GET /health
```

**No authentication required**

**Response:**
```json
{
  "status": "healthy",
  "searxng_connected": true,
  "version": "1.0.0"
}
```

---

### Standard Search

Perform a search and get all results at once.

```http
GET /api/v1/search
```

**Headers:**
- `X-API-Key` (required): Your API key

**Query Parameters:**
- `q` (required, string): Search query
- `limit` (optional, integer): Number of results (default: 10, max: 50)
- `engines` (optional, string): Comma-separated engine names (e.g., "google,duckduckgo")
- `language` (optional, string): Language code (e.g., "en", "es")

**Example Request:**
```bash
curl -H "X-API-Key: your-key" \
  "http://localhost:8000/api/v1/search?q=quantum+computing&limit=5"
```

**Response Schema:**
```json
{
  "query": "string",
  "results": [
    {
      "title": "string",
      "url": "string",
      "content": "string",
      "snippet": "string",
      "metadata": {
        "published_date": "string | null",
        "source": "string",
        "content_type": "string",
        "word_count": "integer | null",
        "credibility_score": "float | null"
      },
      "citation": {
        "apa": "string",
        "mla": "string",
        "chicago": "string"
      },
      "engine": "string"
    }
  ],
  "total_results": "integer",
  "search_time_ms": "integer",
  "engines_used": ["string"]
}
```

**Field Descriptions:**

- `content`: Clean extracted main content without ads, navigation, or scripts
- `snippet`: Short description from search engine
- `metadata.published_date`: ISO 8601 date if detected (e.g., "2024-01-15")
- `metadata.content_type`: Detected type: "article", "documentation", "forum", "video", "pdf", etc.
- `metadata.word_count`: Approximate word count of main content
- `metadata.credibility_score`: 0-1 score based on source domain and other signals
- `citation`: Pre-formatted citations in common academic formats

---

### Streaming Search

Perform a search and stream results as they arrive.

```http
GET /api/v1/search/stream
```

**Headers:**
- `X-API-Key` (required): Your API key

**Query Parameters:**
Same as standard search endpoint

**Response Type:** `text/event-stream` (Server-Sent Events)

**Event Types:**

1. **result** - Individual search result
```
event: result
data: {"title": "...", "url": "...", ...}
```

2. **metadata** - Search metadata
```
event: metadata
data: {"total_results": 10, "search_time_ms": 342}
```

3. **done** - Search complete
```
event: done
data: {"status": "complete"}
```

4. **error** - Error occurred
```
event: error
data: {"error": "Error message"}
```

**Example with curl:**
```bash
curl -N -H "X-API-Key: your-key" \
  "http://localhost:8000/api/v1/search/stream?q=machine+learning&limit=5"
```

**Example with Python (requests):**
```python
import requests
import json

headers = {"X-API-Key": "your-key"}
params = {"q": "machine learning", "limit": 5}

response = requests.get(
    "http://localhost:8000/api/v1/search/stream",
    headers=headers,
    params=params,
    stream=True
)

for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('event: '):
            event_type = line[7:]
        elif line.startswith('data: '):
            data = json.loads(line[6:])
            if event_type == 'result':
                print(f"Got result: {data['title']}")
            elif event_type == 'done':
                print("Search complete!")
```

**Example with JavaScript (fetch):**
```javascript
const response = await fetch(
  'http://localhost:8000/api/v1/search/stream?q=AI&limit=5',
  {
    headers: { 'X-API-Key': 'your-key' }
  }
);

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      console.log('Result:', data);
    }
  }
}
```

---

## Rate Limiting

Default rate limit: 60 requests per minute per API key

When rate limited, you'll receive:
```json
{
  "detail": "Rate limit exceeded. Try again in X seconds."
}
```

**Response Headers:**
- `X-RateLimit-Limit`: Requests allowed per minute
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Human-readable error message",
  "error_code": "ERROR_CODE",
  "request_id": "uuid"
}
```

**Common Error Codes:**

| Status | Code | Description |
|--------|------|-------------|
| 400 | INVALID_QUERY | Query parameter missing or invalid |
| 401 | MISSING_API_KEY | X-API-Key header not provided |
| 403 | INVALID_API_KEY | API key not valid |
| 422 | VALIDATION_ERROR | Request parameters failed validation |
| 429 | RATE_LIMIT_EXCEEDED | Too many requests |
| 500 | INTERNAL_ERROR | Server error |
| 503 | SEARXNG_UNAVAILABLE | SearXNG service unreachable |

---

## Best Practices

### For LLM Integration

1. **Use appropriate result limits**
   - 5-10 results for most queries
   - Consider token limits of your LLM

2. **Extract key information**
   - Use `content` field for main text
   - Use `snippet` for quick summaries
   - Use `metadata.published_date` to filter by recency

3. **Include citations**
   - Always use the `citation` field for source attribution
   - Include URLs in LLM responses

4. **Handle errors gracefully**
   - Implement retry logic with exponential backoff
   - Fall back to alternative search methods if API is down

### Example LLM Prompt Template

```
Search Results for "{query}":

{for each result}
Source {index}: {title}
URL: {url}
Published: {published_date or "Unknown"}
Content: {content[:1000]}...

Citation: {citation.apa}
---
{end for}

Based on these search results, [your instruction to LLM]
```

### Performance Tips

1. **Use streaming for real-time UX**
   - Display results as they arrive
   - Reduce perceived latency

2. **Cache results when appropriate**
   - Search results can be cached for a few minutes
   - Implement client-side caching to reduce API calls

3. **Specify engines for focused searches**
   - Use `engines=google,bing` for general web
   - Use `engines=arxiv,scholar` for academic content
   - Use `engines=github` for code searches

---

## OpenAPI Specification

Interactive API documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Download OpenAPI JSON: http://localhost:8000/openapi.json
