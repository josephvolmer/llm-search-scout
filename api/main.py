"""Main FastAPI application for LLM Search Engine."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from contextlib import asynccontextmanager
import logging
import asyncio
import uvicorn

from config import settings
from models import HealthResponse
from services.searxng_client import searxng_client
from auth import cleanup_old_rate_limit_data
from routers import search, stream

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Background tasks
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting LLM Search API...")
    logger.info(f"SearXNG URL: {settings.searxng_url}")
    logger.info(f"Max results per query: {settings.max_results}")

    # Start background cleanup task
    cleanup_task = asyncio.create_task(cleanup_old_rate_limit_data())

    # Check SearXNG connection
    try:
        is_healthy = await searxng_client.health_check()
        if is_healthy:
            logger.info("Successfully connected to SearXNG")
        else:
            logger.warning("Could not connect to SearXNG - it may not be ready yet")
    except Exception as e:
        logger.error(f"Error checking SearXNG health: {e}")

    yield

    # Shutdown
    logger.info("Shutting down LLM Search API...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


# Create FastAPI app
app = FastAPI(
    title="LLM Search Scout API",
    description="""
    🔍 **LLM Search Scout** - A self-hosted search engine optimized for Large Language Models

    Built on top of SearXNG with:
    - Clean content extraction
    - Rich metadata enrichment
    - Auto-generated citations
    - Optional AI features (summarization, embeddings, deduplication)

    **Documentation:** [GitHub](https://github.com/josephvolmer/llm-search-scout)
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,  # Disable default docs to use custom
    redoc_url=None,  # Disable default redoc to use custom
)

# Mount static files
app.mount("/static", StaticFiles(directory="/app/static"), name="static")

# CORS middleware (allow all origins for self-hosted use)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(search.router)
app.include_router(stream.router)


# Custom Swagger UI with logo
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Documentation",
        swagger_favicon_url="/static/logo.png",
        swagger_ui_parameters={
            "defaultModelsExpandDepth": -1,
            "docExpansion": "list",
            "filter": True,
        },
    )


# Custom ReDoc with logo
@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html():
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{app.title} - Documentation</title>
        <link rel="shortcut icon" href="/static/logo.png">
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
        <redoc spec-url='{app.openapi_url}'></redoc>
        <script src="https://cdn.jsdelivr.net/npm/redoc@latest/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """)


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with basic info."""
    return {
        "name": "LLM Search Scout API",
        "version": "1.0.0",
        "description": "A self-hosted search engine optimized for LLMs",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "logo": "/static/logo.png",
    }


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns service status and SearXNG connectivity.
    """
    searxng_connected = await searxng_client.health_check()

    return HealthResponse(
        status="healthy" if searxng_connected else "degraded",
        searxng_connected=searxng_connected,
        version="1.0.0",
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
        },
    )


# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level,
        reload=False,
    )
