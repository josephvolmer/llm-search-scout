# Integration Examples

Complete code examples for integrating the LLM Search Engine into various applications and frameworks.

## Table of Contents
- [Python Examples](#python-examples)
- [JavaScript/TypeScript](#javascripttypescript)
- [LangChain Integration](#langchain-integration)
- [OpenAI Function Calling](#openai-function-calling)
- [Claude Tool Use](#claude-tool-use)
- [Command Line Tools](#command-line-tools)

---

## Python Examples

### Basic Search Client

```python
import requests
from typing import List, Dict, Optional

class LLMSearchClient:
    """Client for LLM Search Engine API."""

    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}

    def search(
        self,
        query: str,
        limit: int = 10,
        engines: Optional[str] = None,
        language: str = "en"
    ) -> Dict:
        """Perform a search query."""
        params = {
            "q": query,
            "limit": limit,
            "language": language
        }
        if engines:
            params["engines"] = engines

        response = requests.get(
            f"{self.base_url}/api/v1/search",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()

    def search_stream(
        self,
        query: str,
        limit: int = 10,
        engines: Optional[str] = None,
        language: str = "en"
    ):
        """Stream search results."""
        params = {
            "q": query,
            "limit": limit,
            "language": language
        }
        if engines:
            params["engines"] = engines

        response = requests.get(
            f"{self.base_url}/api/v1/search/stream",
            headers=self.headers,
            params=params,
            stream=True
        )
        response.raise_for_status()

        import json
        event_type = None

        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('event: '):
                    event_type = line[7:]
                elif line.startswith('data: '):
                    data = json.loads(line[6:])
                    yield event_type, data

    def format_for_llm(self, results: Dict, max_results: int = 5) -> str:
        """Format search results for LLM context."""
        formatted = [f"Search results for '{results['query']}':\n"]

        for i, result in enumerate(results['results'][:max_results], 1):
            formatted.append(f"\n{i}. {result['title']}")
            formatted.append(f"   URL: {result['url']}")
            formatted.append(f"   Source: {result['metadata']['source']}")

            if result['metadata']['published_date']:
                formatted.append(f"   Published: {result['metadata']['published_date']}")

            formatted.append(f"   Content: {result['content'][:500]}...")
            formatted.append(f"   Citation: {result['citation']['apa']}")

        return '\n'.join(formatted)


# Usage
client = LLMSearchClient(api_key="your-key-here")

# Standard search
results = client.search("machine learning", limit=5)
print(client.format_for_llm(results))

# Streaming search
for event_type, data in client.search_stream("python tutorial", limit=3):
    if event_type == "result":
        print(f"Got result: {data['title']}")
```

### Async Client

```python
import asyncio
import aiohttp
from typing import List, Dict, Optional

class AsyncLLMSearchClient:
    """Async client for LLM Search Engine API."""

    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}

    async def search(
        self,
        query: str,
        limit: int = 10,
        engines: Optional[str] = None
    ) -> Dict:
        """Perform an async search query."""
        params = {"q": query, "limit": limit}
        if engines:
            params["engines"] = engines

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/v1/search",
                headers=self.headers,
                params=params
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def search_multiple(self, queries: List[str]) -> List[Dict]:
        """Search multiple queries concurrently."""
        tasks = [self.search(query) for query in queries]
        return await asyncio.gather(*tasks)


# Usage
async def main():
    client = AsyncLLMSearchClient(api_key="your-key-here")

    # Single search
    results = await client.search("rust programming")
    print(f"Found {results['total_results']} results")

    # Multiple concurrent searches
    queries = ["python", "javascript", "golang"]
    all_results = await client.search_multiple(queries)

    for query, results in zip(queries, all_results):
        print(f"\n{query}: {results['total_results']} results")

asyncio.run(main())
```

---

## JavaScript/TypeScript

### TypeScript Client

```typescript
interface SearchMetadata {
  published_date: string | null;
  source: string;
  content_type: string;
  word_count: number | null;
  credibility_score: number | null;
}

interface Citation {
  apa: string;
  mla: string;
  chicago: string;
}

interface SearchResult {
  title: string;
  url: string;
  content: string;
  snippet: string;
  metadata: SearchMetadata;
  citation: Citation;
  engine: string;
}

interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
  search_time_ms: number;
  engines_used: string[];
}

class LLMSearchClient {
  private apiKey: string;
  private baseUrl: string;

  constructor(apiKey: string, baseUrl: string = 'http://localhost:8000') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
  }

  async search(
    query: string,
    limit: number = 10,
    engines?: string
  ): Promise<SearchResponse> {
    const params = new URLSearchParams({
      q: query,
      limit: limit.toString(),
    });

    if (engines) {
      params.append('engines', engines);
    }

    const response = await fetch(
      `${this.baseUrl}/api/v1/search?${params}`,
      {
        headers: {
          'X-API-Key': this.apiKey,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Search failed: ${response.statusText}`);
    }

    return await response.json();
  }

  async *searchStream(
    query: string,
    limit: number = 10
  ): AsyncGenerator<{ type: string; data: any }> {
    const params = new URLSearchParams({
      q: query,
      limit: limit.toString(),
    });

    const response = await fetch(
      `${this.baseUrl}/api/v1/search/stream?${params}`,
      {
        headers: {
          'X-API-Key': this.apiKey,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Search failed: ${response.statusText}`);
    }

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let eventType = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          eventType = line.slice(7);
        } else if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));
          yield { type: eventType, data };
        }
      }
    }
  }

  formatForLLM(results: SearchResponse, maxResults: number = 5): string {
    const formatted: string[] = [
      `Search results for "${results.query}":\n`,
    ];

    results.results.slice(0, maxResults).forEach((result, i) => {
      formatted.push(`\n${i + 1}. ${result.title}`);
      formatted.push(`   URL: ${result.url}`);
      formatted.push(`   Source: ${result.metadata.source}`);

      if (result.metadata.published_date) {
        formatted.push(`   Published: ${result.metadata.published_date}`);
      }

      formatted.push(`   ${result.content.substring(0, 500)}...`);
      formatted.push(`   Citation: ${result.citation.apa}`);
    });

    return formatted.join('\n');
  }
}

// Usage
const client = new LLMSearchClient('your-key-here');

// Standard search
const results = await client.search('web development', 5);
console.log(client.formatForLLM(results));

// Streaming search
for await (const { type, data } of client.searchStream('AI', 5)) {
  if (type === 'result') {
    console.log(`Got result: ${data.title}`);
  } else if (type === 'done') {
    console.log('Search complete!');
  }
}
```

---

## LangChain Integration

### Basic Tool

```python
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
import requests

API_KEY = "your-search-api-key"
BASE_URL = "http://localhost:8000"

def web_search(query: str) -> str:
    """Search the web using LLM Search Engine."""
    headers = {"X-API-Key": API_KEY}
    params = {"q": query, "limit": 5}

    response = requests.get(
        f"{BASE_URL}/api/v1/search",
        headers=headers,
        params=params
    )

    if response.status_code != 200:
        return f"Search failed: {response.text}"

    results = response.json()

    # Format results for LLM
    formatted = [f"Search results for '{query}':\n"]
    for i, result in enumerate(results['results'], 1):
        formatted.append(
            f"{i}. [{result['title']}]({result['url']})\n"
            f"   {result['content'][:300]}...\n"
        )

    return '\n'.join(formatted)

# Create tool
search_tool = Tool(
    name="WebSearch",
    func=web_search,
    description="Useful for searching the web for current information. "
                "Input should be a search query string."
)

# Initialize agent
llm = ChatOpenAI(temperature=0)
agent = initialize_agent(
    tools=[search_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Use the agent
result = agent.run("What are the latest developments in quantum computing?")
print(result)
```

### Advanced Tool with Citations

```python
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type
import requests

class SearchInput(BaseModel):
    """Input for web search tool."""
    query: str = Field(..., description="The search query")
    limit: int = Field(5, description="Number of results to return")
    engines: Optional[str] = Field(None, description="Comma-separated engine names")

class WebSearchTool(BaseTool):
    """Enhanced web search tool with citations."""

    name = "web_search"
    description = "Search the web for current information with citations"
    args_schema: Type[BaseModel] = SearchInput

    api_key: str = Field(..., description="API key for search service")
    base_url: str = Field(default="http://localhost:8000")

    def _run(self, query: str, limit: int = 5, engines: Optional[str] = None) -> str:
        """Execute the search."""
        headers = {"X-API-Key": self.api_key}
        params = {"q": query, "limit": limit}
        if engines:
            params["engines"] = engines

        response = requests.get(
            f"{self.base_url}/api/v1/search",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        results = response.json()

        # Format with citations
        formatted = [f"Search results for '{query}':\n"]
        citations = []

        for i, result in enumerate(results['results'], 1):
            formatted.append(
                f"\n{i}. {result['title']}\n"
                f"   Source: {result['metadata']['source']}\n"
                f"   Published: {result['metadata']['published_date'] or 'Unknown'}\n"
                f"   Content: {result['content'][:400]}...\n"
            )
            citations.append(f"[{i}] {result['citation']['apa']}")

        formatted.append("\n\nCitations:\n")
        formatted.extend(citations)

        return '\n'.join(formatted)

    async def _arun(self, query: str, limit: int = 5, engines: Optional[str] = None) -> str:
        """Async version."""
        raise NotImplementedError("Async not implemented")

# Usage
search_tool = WebSearchTool(api_key="your-key-here")
result = search_tool.run("climate change latest research")
```

---

## OpenAI Function Calling

```python
import openai
import requests
import json

openai.api_key = "your-openai-key"
SEARCH_API_KEY = "your-search-api-key"

# Define the function
functions = [
    {
        "name": "web_search",
        "description": "Search the web for current information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    }
]

def web_search(query: str, limit: int = 5) -> str:
    """Execute web search."""
    response = requests.get(
        "http://localhost:8000/api/v1/search",
        headers={"X-API-Key": SEARCH_API_KEY},
        params={"q": query, "limit": limit}
    )
    results = response.json()

    # Format for GPT
    formatted = []
    for r in results['results']:
        formatted.append({
            "title": r['title'],
            "url": r['url'],
            "content": r['content'][:500],
            "source": r['metadata']['source'],
            "published": r['metadata']['published_date']
        })

    return json.dumps(formatted, indent=2)

# Chat with function calling
messages = [
    {"role": "user", "content": "What are the best practices for Python async programming in 2024?"}
]

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=messages,
    functions=functions,
    function_call="auto"
)

# Check if function was called
if response.choices[0].message.get("function_call"):
    function_name = response.choices[0].message["function_call"]["name"]
    function_args = json.loads(response.choices[0].message["function_call"]["arguments"])

    if function_name == "web_search":
        function_response = web_search(**function_args)

        # Add function result to messages
        messages.append(response.choices[0].message)
        messages.append({
            "role": "function",
            "name": function_name,
            "content": function_response
        })

        # Get final response
        second_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages
        )

        print(second_response.choices[0].message["content"])
```

---

## Claude Tool Use

```python
import anthropic
import requests
import json

client = anthropic.Anthropic(api_key="your-claude-key")
SEARCH_API_KEY = "your-search-api-key"

# Define tool
tools = [
    {
        "name": "web_search",
        "description": "Search the web for current information with citations",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of results",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    }
]

def web_search(query: str, limit: int = 5):
    """Execute search and return results."""
    response = requests.get(
        "http://localhost:8000/api/v1/search",
        headers={"X-API-Key": SEARCH_API_KEY},
        params={"q": query, "limit": limit}
    )
    return response.json()

# Use Claude with tool
user_message = "What are the latest breakthroughs in fusion energy?"

message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    tools=tools,
    messages=[{"role": "user", "content": user_message}]
)

# Process tool use
if message.stop_reason == "tool_use":
    tool_use = next(block for block in message.content if block.type == "tool_use")

    if tool_use.name == "web_search":
        # Execute search
        search_results = web_search(**tool_use.input)

        # Format results for Claude
        formatted_results = []
        for r in search_results['results']:
            formatted_results.append({
                "title": r['title'],
                "url": r['url'],
                "content": r['content'],
                "citation": r['citation']['apa']
            })

        # Continue conversation with results
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": message.content},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": json.dumps(formatted_results)
                        }
                    ]
                }
            ]
        )

        print(response.content[0].text)
```

---

## Command Line Tools

### Simple CLI

```bash
#!/bin/bash
# llm-search.sh - Simple CLI for LLM Search

API_KEY="${LLM_SEARCH_API_KEY}"
BASE_URL="${LLM_SEARCH_URL:-http://localhost:8000}"

if [ -z "$API_KEY" ]; then
    echo "Error: Set LLM_SEARCH_API_KEY environment variable"
    exit 1
fi

QUERY="$1"
LIMIT="${2:-5}"

if [ -z "$QUERY" ]; then
    echo "Usage: $0 <query> [limit]"
    exit 1
fi

curl -s -H "X-API-Key: $API_KEY" \
    "$BASE_URL/api/v1/search?q=$(echo "$QUERY" | jq -sRr @uri)&limit=$LIMIT" \
    | jq -r '.results[] | "\(.title)\n  \(.url)\n  \(.content[:200])...\n"'
```

### Python CLI with Rich Output

```python
#!/usr/bin/env python3
import click
import requests
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown

console = Console()

@click.command()
@click.argument('query')
@click.option('--limit', '-l', default=5, help='Number of results')
@click.option('--api-key', '-k', envvar='LLM_SEARCH_API_KEY', required=True)
@click.option('--url', '-u', default='http://localhost:8000')
def search(query, limit, api_key, url):
    """Search the web using LLM Search Engine."""

    console.print(f"[bold]Searching for:[/bold] {query}\n")

    response = requests.get(
        f"{url}/api/v1/search",
        headers={"X-API-Key": api_key},
        params={"q": query, "limit": limit}
    )

    if response.status_code != 200:
        console.print(f"[red]Error:[/red] {response.text}")
        return

    results = response.json()

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=3)
    table.add_column("Title")
    table.add_column("Source")
    table.add_column("Published")

    for i, result in enumerate(results['results'], 1):
        table.add_row(
            str(i),
            result['title'],
            result['metadata']['source'],
            result['metadata']['published_date'] or "Unknown"
        )

    console.print(table)
    console.print(f"\n[dim]Found {results['total_results']} results in {results['search_time_ms']}ms[/dim]\n")

    # Show first result details
    if results['results']:
        first = results['results'][0]
        console.print(f"[bold]Top Result:[/bold]")
        console.print(f"URL: {first['url']}")
        console.print(f"\n{first['content'][:500]}...\n")
        console.print(f"[dim]Citation:[/dim] {first['citation']['apa']}")

if __name__ == '__main__':
    search()
```

Save as `llm-search`, make executable, and use:
```bash
chmod +x llm-search
export LLM_SEARCH_API_KEY=your-key
./llm-search "machine learning" --limit 10
```
