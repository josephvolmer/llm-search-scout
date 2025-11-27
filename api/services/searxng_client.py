"""SearXNG client for querying the search engine."""

import httpx
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from config import settings

logger = logging.getLogger(__name__)


class SearXNGClient:
    """Async client for interacting with SearXNG."""

    def __init__(self, base_url: str = None):
        """
        Initialize the SearXNG client.

        Args:
            base_url: Base URL for SearXNG (defaults to settings)
        """
        self.base_url = base_url or settings.searxng_url
        self.timeout = httpx.Timeout(30.0)

    async def search(
        self,
        query: str,
        limit: int = 10,
        engines: Optional[str] = None,
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Perform a search query against SearXNG.

        Args:
            query: Search query string
            limit: Number of results to return
            engines: Comma-separated engine names (optional)
            language: Language code

        Returns:
            Dict containing search results from SearXNG

        Raises:
            httpx.HTTPError: If request fails
        """
        params = {
            "q": query,
            "format": "json",
            "language": language,
        }

        if engines:
            params["engines"] = engines

        start_time = datetime.utcnow()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(f"{self.base_url}/search", params=params)
                response.raise_for_status()
                data = response.json()

                # Calculate search time
                search_time = (datetime.utcnow() - start_time).total_seconds() * 1000

                # Limit results
                if "results" in data:
                    data["results"] = data["results"][:limit]

                # Add timing info
                data["search_time_ms"] = int(search_time)

                return data

            except httpx.HTTPStatusError as e:
                logger.error(f"SearXNG returned error: {e.response.status_code}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Failed to connect to SearXNG: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error during search: {e}")
                raise

    async def health_check(self) -> bool:
        """
        Check if SearXNG is reachable and healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                # Try to access the healthz endpoint or root
                try:
                    response = await client.get(f"{self.base_url}/healthz")
                except httpx.HTTPStatusError:
                    # Try root endpoint if healthz doesn't exist
                    response = await client.get(f"{self.base_url}/")

                return response.status_code == 200
        except Exception as e:
            logger.error(f"SearXNG health check failed: {e}")
            return False

    async def get_enabled_engines(self) -> List[str]:
        """
        Get list of enabled search engines from SearXNG.

        Returns:
            List of engine names
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # SearXNG's config endpoint
                response = await client.get(f"{self.base_url}/config")
                if response.status_code == 200:
                    config = response.json()
                    engines = config.get("engines", [])
                    return [e["name"] for e in engines if not e.get("disabled", False)]
        except Exception as e:
            logger.warning(f"Could not fetch engines list: {e}")

        # Return common engines as fallback
        return [
            "google",
            "duckduckgo",
            "bing",
            "brave",
            "wikipedia",
            "github",
            "stackoverflow",
        ]


# Global client instance
searxng_client = SearXNGClient()
