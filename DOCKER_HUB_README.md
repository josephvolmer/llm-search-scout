# LLM Search Scout

A self-hosted search engine API optimized for Large Language Models, powered by SearXNG.

## ⚖️ License Information

**IMPORTANT**: This image contains software under multiple licenses:

- **LLM Search Scout API**: MIT License
- **SearXNG (included)**: AGPL-3.0 License (used unmodified)

### AGPL-3.0 Compliance

SearXNG is included in this image under the AGPL-3.0 license. In compliance with AGPL-3.0:

- **Source Code Location**: Complete SearXNG source is included at `/usr/local/searxng` within the container
- **Original Source**: https://github.com/searxng/searxng
- **Modifications**: None - SearXNG is used unmodified as a separate network service
- **License Text**: https://github.com/searxng/searxng/blob/master/LICENSE
- **Additional Legal Info**: See `/usr/local/share/licenses/llm-search-scout/NOTICES.md` in the container

Users who download this image have full access to the SearXNG source code within the container.

## 🚀 Quick Start

```bash
# Pull the image
docker pull josephvolmer/llm-search-scout:latest
# OR from GitHub Container Registry
docker pull ghcr.io/josephvolmer/llm-search-scout:latest

# Run with basic configuration
docker run -d \
  --name llm-search \
  -p 8000:8000 \
  -e API_KEYS=your-secure-api-key \
  josephvolmer/llm-search-scout:latest

# Test the API
curl -H "X-API-Key: your-secure-api-key" \
  "http://localhost:8000/health"
```

## ✨ Features

- **Clean Content Extraction**: Removes ads and extracts main content using readability algorithms
- **Rich Metadata**: Publication dates, credibility scores, reading time, keywords, language detection
- **Auto-Generated Citations**: Pre-formatted citations in APA, MLA, and Chicago styles
- **Streaming Support**: Server-Sent Events for real-time result delivery
- **API Key Authentication**: Secure access with configurable rate limiting (60 req/min default)
- **Optional AI Features**: Summarization, embeddings, and semantic deduplication via OpenAI

## 📖 API Documentation

Once running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🔧 Configuration

### Environment Variables

```bash
docker run -d \
  -p 8000:8000 \
  -e API_KEYS=key1,key2 \
  -e MAX_RESULTS=50 \
  -e RATE_LIMIT_PER_MINUTE=60 \
  -e OPENAI_API_KEY=sk-your-key \
  josephvolmer/llm-search-scout:latest
```

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEYS` | Comma-separated API keys | `demo-key-change-this-in-production` |
| `MAX_RESULTS` | Maximum results per query | `50` |
| `DEFAULT_RESULTS` | Default number of results | `10` |
| `RATE_LIMIT_PER_MINUTE` | Rate limit per API key | `60` |
| `MAX_CONTENT_LENGTH` | Max extracted content length | `5000` |
| `OPENAI_API_KEY` | OpenAI API key for AI features (optional) | - |

### Docker Compose

```yaml
version: '3.8'
services:
  llm-search-scout:
    image: josephvolmer/llm-search-scout:latest
    ports:
      - "8000:8000"
    environment:
      - API_KEYS=${API_KEYS}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    restart: unless-stopped
```

## 🔍 Usage Examples

### Basic Search

```bash
curl -H "X-API-Key: your-key" \
  "http://localhost:8000/api/v1/search?q=python+tutorial&limit=5"
```

### With AI Features

```bash
curl -H "X-API-Key: your-key" \
  "http://localhost:8000/api/v1/search?q=quantum+computing&summarize=true&embeddings=true&limit=3"
```

### Streaming Search

```bash
curl -N -H "X-API-Key: your-key" \
  "http://localhost:8000/api/v1/search/stream?q=machine+learning&limit=5"
```

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│  LLM Search Scout API (MIT)     │  ← Your interaction point
│  FastAPI + Content Processing   │  ← Port 8000
└──────────────┬──────────────────┘
               │ HTTP/JSON
┌──────────────▼──────────────────┐
│  SearXNG Service (AGPL-3.0)     │  ← Internal search engine
│  Unmodified, separate process   │  ← Port 8080 (internal)
└─────────────────────────────────┘
```

**Key Points:**
- The MIT-licensed API wrapper and AGPL-licensed SearXNG are **separate programs**
- They communicate via HTTP - no linking or derivative work relationship
- Using the MIT API does not impose AGPL obligations on your code
- Each component retains its original license

## 📦 Available Tags

- `latest` - Latest stable release from main branch
- `1.0.0`, `1.0`, `1` - Semantic version tags
- `main` - Latest build from main branch
- `sha-<commit>` - Specific commit builds

## 🔒 Security

- **API Key Authentication**: All endpoints protected (except `/health`)
- **Rate Limiting**: Per-key request limits prevent abuse
- **Input Validation**: Pydantic models validate all inputs
- **No Data Storage**: Stateless design, no user data stored
- **CORS**: Configurable cross-origin policies

## 📚 Documentation & Support

- **GitHub Repository**: https://github.com/josephvolmer/llm-search-scout
- **Issue Tracker**: https://github.com/josephvolmer/llm-search-scout/issues
- **Contributing**: https://github.com/josephvolmer/llm-search-scout/blob/main/CONTRIBUTING.md
- **License Details**: https://github.com/josephvolmer/llm-search-scout/blob/main/LICENSE

## 🤝 Integration Examples

### Python

```python
import requests

headers = {"X-API-Key": "your-key"}
response = requests.get(
    "http://localhost:8000/api/v1/search",
    headers=headers,
    params={"q": "rust programming", "limit": 5}
)
results = response.json()
```

### JavaScript/TypeScript

```javascript
const response = await fetch(
  'http://localhost:8000/api/v1/search?q=AI&limit=5',
  { headers: { 'X-API-Key': 'your-key' } }
);
const results = await response.json();
```

### LangChain

```python
from langchain.tools import Tool
import requests

def web_search(query: str) -> str:
    response = requests.get(
        "http://localhost:8000/api/v1/search",
        headers={"X-API-Key": "your-key"},
        params={"q": query, "limit": 5}
    )
    return response.json()

search_tool = Tool(
    name="WebSearch",
    func=web_search,
    description="Search for current information"
)
```

## 🔍 Accessing Source Code

To view SearXNG source code inside the container:

```bash
docker exec -it llm-search bash
cd /usr/local/searxng
ls -la

# View license information
cat /usr/local/share/licenses/llm-search-scout/NOTICES.md
```

## ⚙️ Advanced Configuration

### Custom SearXNG Settings

Mount a custom settings file:

```bash
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/custom-settings.yml:/etc/searxng/settings.yml \
  josephvolmer/llm-search-scout:latest
```

### Persistent Logs

Mount a log volume:

```bash
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/logs:/var/log/supervisor \
  josephvolmer/llm-search-scout:latest
```

## 🏷️ Image Labels

This image includes OCI-compliant labels for license compliance:

```bash
docker inspect josephvolmer/llm-search-scout:latest | jq '.[0].Config.Labels'
```

Key labels:
- `org.opencontainers.image.licenses`: `MIT AND AGPL-3.0`
- `com.llmsearchscout.component.searxng.license`: `AGPL-3.0`
- `com.llmsearchscout.component.searxng.modified`: `false`

## 📊 Platforms

This image is built for multiple architectures:
- `linux/amd64` (x86_64)
- `linux/arm64` (ARM 64-bit)

## ⚡ Performance

- **Search latency**: 200-500ms (depends on search engines)
- **Content extraction**: 1-3 seconds per URL (concurrent)
- **Memory usage**: ~350MB (API + SearXNG)
- **CPU usage**: Low when idle, moderate during searches

## 🐛 Troubleshooting

### Container won't start
```bash
docker logs llm-search
```

### Health check failing
```bash
curl http://localhost:8000/health
docker exec llm-search curl http://localhost:8080/search?q=test&format=json
```

### No search results
Check SearXNG logs:
```bash
docker exec llm-search cat /var/log/supervisor/searxng-stderr.log
```

## 📜 Third-Party Software

This image includes:
- **SearXNG** (AGPL-3.0) - Meta search engine
- **FastAPI** (MIT) - Web framework
- **BeautifulSoup4** (MIT) - HTML parsing
- **lxml** (BSD-3-Clause) - XML/HTML processing
- **readability-lxml** (Apache 2.0) - Content extraction

Full license texts available in the container at `/usr/local/share/licenses/llm-search-scout/`

## 💡 Use Cases

- **LLM Tool Calling**: Integrate as a search tool for GPT-4, Claude, or Llama
- **RAG (Retrieval Augmented Generation)**: Provide current web context to LLMs
- **Research Assistant**: Gather citations and sources
- **Custom Search API**: Build privacy-focused search applications
- **Content Aggregation**: Collect and analyze web content

---

<p align="center">
  <strong>Made for LLMs, by humans</strong><br>
  <a href="https://github.com/josephvolmer/llm-search-scout">GitHub</a> •
  <a href="https://github.com/josephvolmer/llm-search-scout/blob/main/LICENSE">License</a> •
  <a href="https://github.com/josephvolmer/llm-search-scout/issues">Issues</a>
</p>
