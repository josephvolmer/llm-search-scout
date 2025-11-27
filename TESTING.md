# Testing Guide

## Quick Start Testing

After running `./quickstart.sh` or `docker-compose up`, test the API with these commands.

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "searxng_connected": true,
  "version": "1.0.0"
}
```

### 2. Basic Search Test

Replace `YOUR_API_KEY` with your actual API key from `.env`:

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8000/api/v1/search?q=python+programming&limit=3"
```

### 3. Streaming Search Test

```bash
curl -N -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8000/api/v1/search/stream?q=artificial+intelligence&limit=3"
```

## Detailed Testing

### Testing with Different Parameters

**Limit results:**
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8000/api/v1/search?q=javascript&limit=5"
```

**Specify search engines:**
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8000/api/v1/search?q=machine+learning&engines=google,duckduckgo&limit=5"
```

**Different language:**
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8000/api/v1/search?q=programación&language=es&limit=3"
```

### Testing Authentication

**Missing API key (should fail with 401):**
```bash
curl "http://localhost:8000/api/v1/search?q=test"
```

**Invalid API key (should fail with 403):**
```bash
curl -H "X-API-Key: invalid-key" \
  "http://localhost:8000/api/v1/search?q=test"
```

### Testing Rate Limiting

Send multiple rapid requests to trigger rate limiting:

```bash
for i in {1..65}; do
  echo "Request $i"
  curl -H "X-API-Key: YOUR_API_KEY" \
    "http://localhost:8000/api/v1/search?q=test&limit=1"
  echo ""
done
```

After 60 requests in a minute, you should receive a 429 error.

## Python Testing Examples

### Standard Search

```python
import requests

API_KEY = "your-api-key-here"
BASE_URL = "http://localhost:8000"

headers = {"X-API-Key": API_KEY}
params = {
    "q": "python web scraping",
    "limit": 5
}

response = requests.get(
    f"{BASE_URL}/api/v1/search",
    headers=headers,
    params=params
)

results = response.json()
print(f"Found {results['total_results']} results")

for result in results['results']:
    print(f"\nTitle: {result['title']}")
    print(f"URL: {result['url']}")
    print(f"Source: {result['metadata']['source']}")
    print(f"Published: {result['metadata']['published_date']}")
    print(f"Content preview: {result['content'][:200]}...")
    print(f"APA Citation: {result['citation']['apa']}")
```

### Streaming Search

```python
import requests
import json

API_KEY = "your-api-key-here"
BASE_URL = "http://localhost:8000"

headers = {"X-API-Key": API_KEY}
params = {"q": "machine learning", "limit": 5}

response = requests.get(
    f"{BASE_URL}/api/v1/search/stream",
    headers=headers,
    params=params,
    stream=True
)

event_type = None
for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')

        if line.startswith('event: '):
            event_type = line[7:]
        elif line.startswith('data: '):
            data = json.loads(line[6:])

            if event_type == 'result':
                print(f"\nGot result: {data['title']}")
                print(f"  URL: {data['url']}")
            elif event_type == 'metadata':
                print(f"\nSearch complete: {data['total_results']} results in {data['search_time_ms']}ms")
            elif event_type == 'done':
                print("\nStream finished!")
            elif event_type == 'error':
                print(f"\nError: {data['error']}")
```

### Using with LangChain

```python
from langchain.tools import Tool
import requests

API_KEY = "your-api-key-here"
BASE_URL = "http://localhost:8000"

def search_web(query: str) -> str:
    """Search the web and return formatted results for LLM."""
    headers = {"X-API-Key": API_KEY}
    params = {"q": query, "limit": 5}

    response = requests.get(
        f"{BASE_URL}/api/v1/search",
        headers=headers,
        params=params
    )

    if response.status_code != 200:
        return f"Search failed: {response.text}"

    results = response.json()["results"]

    # Format for LLM consumption
    formatted = []
    for i, r in enumerate(results, 1):
        formatted.append(
            f"{i}. [{r['title']}]({r['url']})\n"
            f"   Source: {r['metadata']['source']}\n"
            f"   Published: {r['metadata']['published_date'] or 'Unknown'}\n"
            f"   {r['content'][:300]}...\n"
        )

    return "\n".join(formatted)

# Create LangChain tool
search_tool = Tool(
    name="WebSearch",
    func=search_web,
    description="Search the web for current information. Input should be a search query string."
)

# Use with LangChain agent
tools = [search_tool]
# ... rest of LangChain setup
```

## JavaScript/TypeScript Testing

```typescript
// Standard search
async function searchWeb(query: string, limit: number = 10) {
  const response = await fetch(
    `http://localhost:8000/api/v1/search?q=${encodeURIComponent(query)}&limit=${limit}`,
    {
      headers: {
        'X-API-Key': 'your-api-key-here'
      }
    }
  );

  const data = await response.json();
  return data;
}

// Streaming search
async function streamSearch(query: string, limit: number = 10) {
  const response = await fetch(
    `http://localhost:8000/api/v1/search/stream?q=${encodeURIComponent(query)}&limit=${limit}`,
    {
      headers: {
        'X-API-Key': 'your-api-key-here'
      }
    }
  );

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();

  let eventType = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('event: ')) {
        eventType = line.slice(7);
      } else if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));

        if (eventType === 'result') {
          console.log('Result:', data.title);
        } else if (eventType === 'metadata') {
          console.log('Total results:', data.total_results);
        } else if (eventType === 'done') {
          console.log('Stream complete!');
        }
      }
    }
  }
}

// Usage
searchWeb('rust programming', 5)
  .then(results => console.log(results));

streamSearch('web development', 5);
```

## Troubleshooting Tests

### If health check fails:

1. Check if containers are running:
   ```bash
   docker-compose ps
   ```

2. Check logs:
   ```bash
   docker-compose logs api
   docker-compose logs searxng
   ```

3. Restart services:
   ```bash
   docker-compose restart
   ```

### If search returns no results:

1. Check SearXNG is working:
   ```bash
   curl "http://localhost:8080/search?q=test&format=json"
   ```

2. Check API logs for errors:
   ```bash
   docker-compose logs -f api
   ```

### If content extraction is slow:

- Content extraction happens in real-time and can take a few seconds per URL
- Use the streaming endpoint for better perceived performance
- Adjust `EXTRACT_TIMEOUT_SECONDS` in `.env` if needed

## Performance Testing

### Test concurrent requests:

```bash
# Install Apache Bench (if not already installed)
# macOS: brew install httpd
# Ubuntu: apt-get install apache2-utils

ab -n 100 -c 10 -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8000/api/v1/search?q=test&limit=3"
```

This sends 100 requests with 10 concurrent connections.

### Monitor resource usage:

```bash
docker stats
```

Shows real-time CPU, memory, and network usage for containers.
