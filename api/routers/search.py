"""Standard search endpoint router."""

from fastapi import APIRouter, Depends, Query, HTTPException, Response
from typing import Optional
import logging
import asyncio

from models import SearchResponse, SearchResult, SearchMetadata, Citation
from auth import verify_api_key_with_rate_limit
from services.searxng_client import searxng_client
from services.content_extractor import content_extractor
from services.metadata_enricher import metadata_enricher
from services.citation_formatter import citation_formatter
from services.ai_service import ai_service
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.get("/search", response_model=SearchResponse)
async def search(
    response: Response,
    q: str = Query(..., description="Search query", min_length=1, max_length=500),
    limit: int = Query(
        settings.default_results,
        description="Number of results",
        ge=1,
        le=settings.max_results,
    ),
    engines: Optional[str] = Query(None, description="Comma-separated engine names"),
    language: str = Query("en", description="Language code"),
    summarize: bool = Query(False, description="Generate AI summaries (requires OpenAI API key)"),
    embeddings: bool = Query(False, description="Compute embeddings (requires OpenAI API key)"),
    dedup: bool = Query(False, description="Remove semantic duplicates using embeddings (requires OpenAI API key)"),
    auth_data: tuple = Depends(verify_api_key_with_rate_limit),
):
    """
    Perform a web search with LLM-optimized results.

    Returns clean, structured results with extracted content, metadata, and citations.
    """
    api_key, rate_limit_headers = auth_data

    # Add rate limit headers to response
    for key, value in rate_limit_headers.items():
        response.headers[key] = value

    # Check if AI features are requested but not available
    ai_requested = summarize or embeddings or dedup
    if ai_requested and not settings.has_openai:
        raise HTTPException(
            status_code=400,
            detail="AI features requested but OpenAI API key is not configured",
        )

    # Deduplication requires embeddings
    if dedup and not embeddings:
        raise HTTPException(
            status_code=400,
            detail="Deduplication requires embeddings=true",
        )

    try:
        # Query SearXNG
        logger.info(f"Searching for: {q} (limit={limit}, engines={engines}, summarize={summarize}, embeddings={embeddings}, dedup={dedup})")
        searxng_results = await searxng_client.search(
            query=q, limit=limit, engines=engines, language=language
        )

        if "results" not in searxng_results or not searxng_results["results"]:
            return SearchResponse(
                query=q,
                results=[],
                total_results=0,
                search_time_ms=searxng_results.get("search_time_ms", 0),
                engines_used=[],
            )

        # Process results in parallel
        raw_results = searxng_results["results"]
        processed_results = await _process_results(
            raw_results,
            summarize=summarize,
            embeddings=embeddings,
            dedup=dedup
        )

        # Extract engines used
        engines_used = list(set(r.get("engine", "unknown") for r in raw_results))

        return SearchResponse(
            query=q,
            results=processed_results,
            total_results=len(processed_results),
            search_time_ms=searxng_results.get("search_time_ms", 0),
            engines_used=engines_used,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


async def _process_results(
    raw_results: list,
    summarize: bool = False,
    embeddings: bool = False,
    dedup: bool = False
) -> list[SearchResult]:
    """
    Process raw SearXNG results into LLM-optimized format.

    Args:
        raw_results: Raw results from SearXNG
        summarize: Generate AI summaries
        embeddings: Compute embeddings
        dedup: Remove semantic duplicates

    Returns:
        List of processed SearchResult objects
    """
    # Extract content from ALL URLs concurrently
    urls_to_extract = [r.get("url") for r in raw_results]
    extracted_content = await content_extractor.batch_extract(urls_to_extract)

    # Process all results in parallel
    tasks = []
    for result in raw_results:
        tasks.append(_process_single_result(result, extracted_content))

    processed_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out exceptions and None results
    processed = []
    for result in processed_results:
        if isinstance(result, Exception):
            logger.error(f"Error processing result: {result}")
            continue
        if result is not None:
            processed.append(result)

    # Apply AI features if requested
    if summarize or embeddings:
        processed = await _apply_ai_features(processed, summarize, embeddings)

    # Apply deduplication if requested
    if dedup and embeddings:
        processed = _deduplicate_results(processed)

    return processed


async def _process_single_result(
    result: dict,
    extracted_content: dict
) -> SearchResult:
    """
    Process a single search result.

    Args:
        result: Raw result from SearXNG
        extracted_content: Pre-fetched content for all URLs

    Returns:
        Processed SearchResult
    """
    try:
        url = result.get("url", "")
        title = result.get("title", "Untitled")
        snippet = result.get("content", "")[:500]  # Limit snippet length

        # Get extracted content or fall back to snippet
        extracted = extracted_content.get(url, {})
        content = extracted.get("content") or snippet or "No content available."

        # Use extracted title if available
        if extracted.get("title"):
            title = extracted["title"]

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
        search_result = SearchResult(
            title=title,
            url=url,
            content=content,
            snippet=snippet,
            metadata=SearchMetadata(**metadata_dict),
            citation=Citation(**citations_dict),
            engine=result.get("engine", "unknown"),
            summary=None,
            embedding=None,
        )

        return search_result

    except Exception as e:
        logger.error(f"Error processing result {result.get('url')}: {e}")
        return None


async def _apply_ai_features(
    results: list[SearchResult],
    summarize: bool,
    embeddings: bool
) -> list[SearchResult]:
    """
    Apply AI features (summarization and embeddings) to results.

    Args:
        results: List of search results
        summarize: Whether to generate summaries
        embeddings: Whether to generate embeddings

    Returns:
        Updated results with AI features
    """
    # Generate embeddings in batch (more efficient)
    result_embeddings = []
    if embeddings:
        texts_to_embed = [f"{r.title}\n\n{r.content}" for r in results]
        result_embeddings = await ai_service.generate_embeddings_batch(texts_to_embed)
    else:
        result_embeddings = [None] * len(results)

    # Generate summaries concurrently (OpenAI doesn't support batch for chat completions)
    summary_tasks = []
    if summarize:
        for result in results:
            summary_tasks.append(ai_service.summarize_content(result.content, result.title))
        result_summaries = await asyncio.gather(*summary_tasks, return_exceptions=True)
        # Convert exceptions to None
        result_summaries = [s if not isinstance(s, Exception) else None for s in result_summaries]
    else:
        result_summaries = [None] * len(results)

    # Combine results with AI features
    updated_results = []
    for result, summary, embedding in zip(results, result_summaries, result_embeddings):
        updated_result = SearchResult(
            title=result.title,
            url=result.url,
            content=result.content,
            snippet=result.snippet,
            metadata=result.metadata,
            citation=result.citation,
            engine=result.engine,
            summary=summary,
            embedding=embedding,
        )
        updated_results.append(updated_result)

    return updated_results


def _deduplicate_results(results: list[SearchResult]) -> list[SearchResult]:
    """
    Remove duplicate results based on embedding similarity.

    Args:
        results: List of search results with embeddings

    Returns:
        Deduplicated list of results
    """
    # Extract embeddings with indices
    results_with_embeddings = [
        (i, result.embedding) for i, result in enumerate(results)
    ]

    # Get indices to keep
    keep_indices = ai_service.deduplicate_by_embeddings(
        results_with_embeddings, threshold=0.95
    )

    # Filter results
    deduplicated = [results[i] for i in keep_indices]
    logger.info(f"Deduplicated {len(results)} -> {len(deduplicated)} results")

    return deduplicated
