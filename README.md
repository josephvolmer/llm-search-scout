# 🔍 LLM Search Scout

<p align="center">
  <img src="docs/logo.png" width="200" alt="LLM Search Scout Logo">
</p>

<p align="center">
  <strong>A self-hosted search engine optimized for Large Language Models</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#api-documentation">API Docs</a> •
  <a href="#ai-features">AI Features</a> •
  <a href="#configuration">Configuration</a>
</p>

---

## Overview

LLM Search Scout is a self-hosted search API designed specifically for LLM consumption. Built on top of [SearXNG](https://github.com/searxng/searxng), it enriches search results with clean content extraction, rich metadata, citations, and optional AI-powered features like summarization and semantic deduplication.

## Features

### 🎯 Core Features
- **Clean Content Extraction**: Strips ads and extracts main content using readability algorithms
- **Rich Metadata**: Publication dates, credibility scores, language detection, reading time, keywords
- **Auto-Generated Citations**: APA, MLA, and Chicago format citations
- **Multiple Search Engines**: Aggregates results from Google, Bing, DuckDuckGo, Brave, and more
- **Rate Limiting**: Built-in per-key rate limiting (60 req/min default)
- **API Key Authentication**: Secure access control
- **Streaming Support**: Server-Sent Events for real-time results

### 🤖 AI-Powered Features (Optional)
- **AI Summarization**: Generate concise summaries using OpenAI GPT-4o-mini
- **Vector Embeddings**: Compute embeddings for semantic analysis
- **Semantic Deduplication**: Remove near-duplicate results using cosine similarity

### 📊 Enhanced Metadata
Each search result includes:
- **Language Detection**: Automatic language identification (English, Spanish, French, German)
- **Reading Time**: Estimated reading time in minutes (225 WPM)
- **Keyword Extraction**: Top 10 keywords from content (title weighted 3x)
- **Direct Answer Detection**: Flags results that appear to directly answer queries
- **Credibility Score**: Source reliability rating (0-1) based on domain reputation
- **Content Type**: Article, documentation, forum, tutorial, video, PDF, etc.

## Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API key (optional, only for AI features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/josephvolmer/llm-search-scout.git
   cd llm-search-scout
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and set your API keys
   ```

3. **Start the services**
   ```bash
   docker compose up -d
   ```

4. **Verify it's running**
   ```bash
   curl -H "X-API-Key: demo-key-change-this-in-production" \
     "http://localhost:8000/health"
   ```

The API will be available at `http://localhost:8000`

## API Documentation

### Authentication
All requests require an API key via the `X-API-Key` header.

```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/search?q=python+programming"
```

### Endpoints

#### `GET /api/v1/search`
Perform a web search with LLM-optimized results.

**Query Parameters:**
- `q` (required): Search query
- `limit` (optional): Number of results (1-50, default: 10)
- `engines` (optional): Comma-separated engine names
- `language` (optional): Language code (default: "en")
- `summarize` (optional): Generate AI summaries (default: false) *requires OpenAI*
- `embeddings` (optional): Compute vector embeddings (default: false) *requires OpenAI*
- `dedup` (optional): Remove semantic duplicates (default: false) *requires embeddings*

**Example Request:**
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/search?q=python+tutorial&limit=5"
```

**Example Response:**
```json
{
  "query": "python tutorial",
  "results": [
    {
      "title": "Python Tutorial",
      "url": "https://www.w3schools.com/python/",
      "content": "Python is a popular programming language...",
      "snippet": "Learn Python programming...",
      "metadata": {
        "published_date": "2024-01-15",
        "source": "w3schools.com",
        "content_type": "tutorial",
        "word_count": 273,
        "credibility_score": 0.75,
        "language": "en",
        "reading_time_minutes": 2,
        "keywords": ["python", "tutorial", "programming"],
        "is_direct_answer": false
      },
      "citation": {
        "apa": "W3schools. (2024). Python Tutorial. w3schools.com. https://...",
        "mla": "W3schools. \"Python Tutorial\" w3schools.com, 2024, https://...",
        "chicago": "W3schools. \"Python Tutorial\" w3schools.com. 2024. https://..."
      },
      "engine": "bing",
      "summary": null,
      "embedding": null
    }
  ],
  "total_results": 5,
  "search_time_ms": 1234,
  "engines_used": ["bing", "google", "duckduckgo"]
}
```

#### `GET /api/v1/search/stream`
Stream search results as they arrive (Server-Sent Events).

```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/search/stream?q=python&limit=5"
```

#### `GET /health`
Health check endpoint (no auth required).

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "searxng_connected": true,
  "version": "1.0.0"
}
```

## AI Features

LLM Search Scout supports optional AI-powered features using OpenAI's API.

### Setup
1. Add your OpenAI API key to `.env`:
   ```bash
   OPENAI_API_KEY=sk-...
   ```

2. Restart the container:
   ```bash
   docker compose restart
   ```

### AI Summarization
Generate concise summaries of search results:

```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/search?q=quantum+computing&summarize=true&limit=3"
```

Each result will include a `summary` field with a 2-3 sentence AI-generated summary using GPT-4o-mini.

### Vector Embeddings
Compute embeddings for semantic analysis:

```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/search?q=machine+learning&embeddings=true&limit=5"
```

Each result will include an `embedding` field with a 1536-dimensional vector using `text-embedding-3-small`.

### Semantic Deduplication
Remove near-duplicate results using embedding similarity:

```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/search?q=neural+networks&embeddings=true&dedup=true&limit=10"
```

Results with >95% cosine similarity will be automatically filtered out, keeping only the most unique results.

### Combined AI Features
Use all AI features together:

```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/search?q=artificial+intelligence&summarize=true&embeddings=true&dedup=true&limit=10"
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# API Configuration
API_KEYS=your-secure-key-1,your-secure-key-2
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=info

# SearXNG Configuration
SEARXNG_URL=http://searxng:8080

# Search Configuration
MAX_RESULTS=50
DEFAULT_RESULTS=10
RATE_LIMIT_PER_MINUTE=60

# Content Extraction
MAX_CONTENT_LENGTH=5000
EXTRACT_TIMEOUT_SECONDS=10

# AI Features (Optional)
OPENAI_API_KEY=sk-your-key-here
```

### Generating Secure API Keys
```bash
openssl rand -hex 32
```

### Customizing Search Engines

Edit `searxng/settings.yml` to configure which search engines to use. See [SearXNG documentation](https://docs.searxng.org/) for details.

## Architecture

```
┌─────────────────┐
│   LLM Client    │
└────────┬────────┘
         │
         │ HTTP/REST
         │
┌────────▼────────┐
│ Search Scout    │
│   FastAPI API   │
├─────────────────┤
│ • Auth & Rate   │
│   Limiting      │
│ • Content       │
│   Extraction    │
│ • Metadata      │
│   Enrichment    │
│ • AI Features   │
│   (Optional)    │
└────────┬────────┘
         │
         │ JSON API
         │
┌────────▼────────┐
│    SearXNG      │
│  Meta Search    │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│ Google │ │  Bing  │  ... (10+ engines)
└────────┘ └────────┘
```

## Development

### Project Structure
```
llm-search-scout/
├── api/
│   ├── main.py              # FastAPI app
│   ├── models.py            # Pydantic models
│   ├── config.py            # Configuration
│   ├── auth.py              # Authentication & rate limiting
│   ├── routers/
│   │   ├── search.py        # Search endpoints
│   │   └── stream.py        # Streaming endpoints
│   └── services/
│       ├── searxng_client.py       # SearXNG integration
│       ├── content_extractor.py    # Web scraping
│       ├── metadata_enricher.py    # Metadata extraction
│       ├── citation_formatter.py   # Citation generation
│       └── ai_service.py           # AI features (OpenAI)
├── searxng/
│   └── settings.yml         # SearXNG configuration
├── docs/
│   └── logo.png             # Project logo
├── docker-compose.yml
├── Dockerfile
├── .env                     # Environment variables (create from .env.example)
└── README.md
```

### Running Tests
```bash
# Test basic search
curl -H "X-API-Key: demo-key-change-this-in-production" \
  "http://localhost:8000/api/v1/search?q=test&limit=1"

# Test streaming
curl -H "X-API-Key: demo-key-change-this-in-production" \
  "http://localhost:8000/api/v1/search/stream?q=test&limit=2"

# Test AI features (requires OpenAI API key)
curl -H "X-API-Key: demo-key-change-this-in-production" \
  "http://localhost:8000/api/v1/search?q=test&summarize=true&embeddings=true&limit=1"
```

### Logs
```bash
# View all logs
docker compose logs -f

# View API logs
docker compose exec llm-search cat /var/log/supervisor/api-stdout.log

# View API errors
docker compose exec llm-search cat /var/log/supervisor/api-stderr.log
```

## Interactive API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Performance

- **Concurrent Content Extraction**: Fetches multiple URLs in parallel
- **Async/Await**: Full async support for maximum throughput
- **Rate Limiting**: Protects against abuse
- **Streaming**: Server-Sent Events for progressive loading
- **AI Batching**: Processes AI requests concurrently

## Security

- **API Key Authentication**: All endpoints protected (except /health)
- **Rate Limiting**: Per-key request limits (60/min default)
- **Input Validation**: Pydantic models validate all inputs
- **CORS**: Configurable cross-origin policies
- **No Data Storage**: Stateless design, no user data stored

## Troubleshooting

### Connection Issues

```bash
# Check if containers are running
docker compose ps

# Check logs
docker compose logs --tail=50

# Restart services
docker compose restart
```

### No Search Results

- Check SearXNG is configured with active engines
- Verify network connectivity from containers
- Review SearXNG logs: `docker compose logs searxng`

### Authentication Errors

If you get 401/403 errors:
- Verify API key matches the one in `.env`
- Check the `X-API-Key` header is correctly set
- Ensure containers were restarted after `.env` changes

### AI Features Not Working

If AI features return errors:
- Verify `OPENAI_API_KEY` is set in `.env`
- Check OpenAI API key is valid
- Restart container: `docker compose restart`
- Check logs for OpenAI errors

## Roadmap

- [ ] Redis-backed rate limiting for multi-instance deployments
- [ ] Custom search engine profiles
- [ ] Result caching layer
- [ ] Webhook support for async searches
- [ ] More AI providers (Anthropic Claude, local models)
- [ ] Image search support
- [ ] News-specific optimizations
- [ ] Fact extraction and verification

## Contributing

Contributions welcome! Please feel free to submit issues and pull requests.

## License

LLM Search Scout is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

### Third-Party Components

This project uses SearXNG as a separate network service:
- **SearXNG** is licensed under **AGPL-3.0** and is used unmodified as a containerized service
- SearXNG source code: https://github.com/searxng/searxng
- Our FastAPI wrapper and content extraction code are MIT-licensed
- SearXNG runs as a separate process and is not modified by this project

Additional dependencies and their licenses are listed in [THIRD_PARTY_LICENSES](THIRD_PARTY_LICENSES).

**Important**: While LLM Search Scout's code is MIT-licensed, SearXNG (which runs as a separate service in the Docker container) is AGPL-3.0. Users deploying this project must comply with SearXNG's AGPL-3.0 license for that component. Since SearXNG is not modified and runs as a separate network service, this does not impose AGPL requirements on your use of the LLM Search Scout API wrapper.

## Acknowledgments

- [SearXNG](https://github.com/searxng/searxng) - Privacy-respecting meta search engine
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Readability](https://github.com/buriy/python-readability) - Content extraction
- [OpenAI](https://openai.com/) - AI features

---

<p align="center">
  Made with 🔍 for LLMs
</p>
