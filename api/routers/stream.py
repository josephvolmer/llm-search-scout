"""Streaming search endpoint router."""

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, AsyncGenerator
import logging
import json
import asyncio

from auth import verify_api_key_with_rate_limit
from services.searxng_client import searxng_client
from services.content_extractor import content_extractor
from services.metadata_enricher import metadata_enricher
from services.citation_formatter import citation_formatter
from config import settings
from models import SearchResult, SearchMetadata, Citation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.get("/search/stream")
async def search_stream(
    q: str = Query(..., description="Search query", min_length=1, max_length=500),
    limit: int = Query(
        settings.default_results,
        description="Number of results",
        ge=1,
        le=settings.max_results,
    ),
    engines: Optional[str] = Query(None, description="Comma-separated engine names"),
    language: str = Query("en", description="Language code"),
    auth_data: tuple = Depends(verify_api_key_with_rate_limit),
):
    """
    Perform a web search with streaming results.

    Returns results as Server-Sent Events (SSE) as they are processed.
    """
    api_key, rate_limit_headers = auth_data

    # Create the streaming response
    return StreamingResponse(
        _stream_search_results(q, limit, engines, language),
        media_type="text/event-stream",
        headers=rate_limit_headers,
    )


async def _stream_search_results(
    query: str, limit: int, engines: Optional[str], language: str
) -> AsyncGenerator[str, None]:
    """
    Generator function that streams search results as SSE events.

    Args:
        query: Search query
        limit: Result limit
        engines: Engine filter
        language: Language code

    Yields:
        SSE formatted strings
    """
    try:
        # Query SearXNG
        logger.info(f"Streaming search for: {query} (limit={limit})")
        searxng_results = await searxng_client.search(
            query=query, limit=limit, engines=engines, language=language
        )

        if "results" not in searxng_results or not searxng_results["results"]:
            # Send empty completion
            yield _format_sse("metadata", {
                "total_results": 0,
                "search_time_ms": searxng_results.get("search_time_ms", 0)
            })
            yield _format_sse("done", {"status": "complete"})
            return

        raw_results = searxng_results["results"]

        # Process and stream each result as it's ready
        for result in raw_results:
            try:
                processed = await _process_single_result(result)
                if processed:
                    # Send result event
                    yield _format_sse("result", processed.model_dump())

            except Exception as e:
                logger.error(f"Error processing result {result.get('url')}: {e}")
                # Send error event but continue
                yield _format_sse("error", {
                    "error": f"Failed to process result: {str(e)}",
                    "url": result.get("url")
                })

        # Send metadata event
        engines_used = list(set(r.get("engine", "unknown") for r in raw_results))
        yield _format_sse("metadata", {
            "total_results": len(raw_results),
            "search_time_ms": searxng_results.get("search_time_ms", 0),
            "engines_used": engines_used
        })

        # Send completion event
        yield _format_sse("done", {"status": "complete"})

    except Exception as e:
        logger.error(f"Stream search error: {e}", exc_info=True)
        yield _format_sse("error", {"error": str(e)})
        yield _format_sse("done", {"status": "error"})


async def _process_single_result(result: dict) -> Optional[SearchResult]:
    """
    Process a single search result.

    Args:
        result: Raw SearXNG result

    Returns:
        Processed SearchResult or None if processing fails
    """
    try:
        url = result.get("url", "")
        title = result.get("title", "Untitled")
        snippet = result.get("content", "")[:500]

        # Extract content (with timeout)
        try:
            extracted = await asyncio.wait_for(
                content_extractor.extract_from_url(url),
                timeout=settings.extract_timeout_seconds
            )
            content = extracted.get("content") or snippet or "No content available."
            if extracted.get("title"):
                title = extracted["title"]
        except asyncio.TimeoutError:
            logger.warning(f"Content extraction timeout for {url}")
            content = snippet or "No content available."
        except Exception as e:
            logger.warning(f"Content extraction failed for {url}: {e}")
            content = snippet or "No content available."

        # Enrich with metadata
        metadata_dict = metadata_enricher.enrich(result, content)

        # Generate citations
        citations_dict = citation_formatter.format_citations(
            title=title,
            url=url,
            source=metadata_dict["source"],
            published_date=metadata_dict["published_date"],
        )

        # Create structured result
        return SearchResult(
            title=title,
            url=url,
            content=content,
            snippet=snippet,
            metadata=SearchMetadata(**metadata_dict),
            citation=Citation(**citations_dict),
            engine=result.get("engine", "unknown"),
        )

    except Exception as e:
        logger.error(f"Failed to process result: {e}")
        return None


def _format_sse(event: str, data: dict) -> str:
    """
    Format data as Server-Sent Event.

    Args:
        event: Event type
        data: Event data

    Returns:
        SSE formatted string
    """
    json_data = json.dumps(data)
    return f"event: {event}\ndata: {json_data}\n\n"
