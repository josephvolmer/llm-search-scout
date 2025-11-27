"""Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime


class SearchMetadata(BaseModel):
    """Metadata about a search result."""

    published_date: Optional[str] = Field(
        None, description="Publication date in ISO 8601 format"
    )
    source: str = Field(..., description="Source domain (e.g., 'example.com')")
    content_type: str = Field(
        "webpage", description="Type of content: article, documentation, forum, etc."
    )
    word_count: Optional[int] = Field(None, description="Approximate word count")
    credibility_score: Optional[float] = Field(
        None, ge=0, le=1, description="Credibility score from 0 to 1"
    )
    language: Optional[str] = Field(None, description="Detected language code (e.g., 'en', 'es')")
    reading_time_minutes: Optional[int] = Field(None, description="Estimated reading time in minutes")
    keywords: Optional[List[str]] = Field(None, description="Top keywords extracted from content")
    is_direct_answer: bool = Field(False, description="Whether this appears to be a direct answer")


class Citation(BaseModel):
    """Pre-formatted citations in common formats."""

    apa: str = Field(..., description="APA format citation")
    mla: str = Field(..., description="MLA format citation")
    chicago: str = Field(..., description="Chicago format citation")


class SearchResult(BaseModel):
    """A single search result with LLM-optimized fields."""

    title: str = Field(..., description="Page title")
    url: str = Field(..., description="Full URL")
    content: str = Field(..., description="Clean extracted main content")
    snippet: str = Field(..., description="Brief description from search engine")
    metadata: SearchMetadata = Field(..., description="Rich metadata")
    citation: Citation = Field(..., description="Pre-formatted citations")
    engine: str = Field(..., description="Search engine that provided this result")
    summary: Optional[str] = Field(None, description="AI-generated summary (if requested)")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding (if requested)")


class SearchResponse(BaseModel):
    """Response from a standard search request."""

    query: str = Field(..., description="Original search query")
    results: List[SearchResult] = Field(..., description="List of search results")
    total_results: int = Field(..., description="Total number of results returned")
    search_time_ms: int = Field(..., description="Search execution time in milliseconds")
    engines_used: List[str] = Field(..., description="List of engines that were queried")


class SearchRequest(BaseModel):
    """Request parameters for search."""

    q: str = Field(..., min_length=1, max_length=500, description="Search query")
    limit: int = Field(10, ge=1, le=50, description="Number of results to return")
    engines: Optional[str] = Field(
        None, description="Comma-separated list of engines to use"
    )
    language: Optional[str] = Field("en", description="Language code (e.g., 'en', 'es')")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    searxng_connected: bool = Field(..., description="Whether SearXNG is reachable")
    version: str = Field("1.0.0", description="API version")


class ErrorResponse(BaseModel):
    """Error response format."""

    detail: str = Field(..., description="Human-readable error message")
    error_code: str = Field(..., description="Machine-readable error code")
    request_id: Optional[str] = Field(None, description="Request tracking ID")


class StreamEvent(BaseModel):
    """Base class for streaming events."""

    pass


class ResultStreamEvent(SearchResult):
    """Individual result in stream."""

    pass


class MetadataStreamEvent(BaseModel):
    """Metadata event in stream."""

    total_results: int
    search_time_ms: int


class DoneStreamEvent(BaseModel):
    """Stream completion event."""

    status: str = "complete"


class ErrorStreamEvent(BaseModel):
    """Error event in stream."""

    error: str
