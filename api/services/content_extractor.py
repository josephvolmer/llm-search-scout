"""Content extraction service for cleaning and extracting main content from web pages."""

import httpx
import asyncio
from bs4 import BeautifulSoup
from readability import Document
import html2text
from typing import Optional, Dict
import logging
from urllib.parse import urlparse

from config import settings

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Extract clean content from web pages."""

    def __init__(self):
        """Initialize the content extractor."""
        self.timeout = httpx.Timeout(settings.extract_timeout_seconds)
        self.max_length = settings.max_content_length

        # Configure html2text for clean markdown conversion
        self.html_to_text = html2text.HTML2Text()
        self.html_to_text.ignore_links = False
        self.html_to_text.ignore_images = True
        self.html_to_text.ignore_emphasis = False
        self.html_to_text.body_width = 0  # No wrapping
        self.html_to_text.single_line_break = True

    async def extract_from_url(self, url: str) -> Dict[str, Optional[str]]:
        """
        Extract clean content from a URL.

        Args:
            url: The URL to extract content from

        Returns:
            Dict with 'content' and 'title' keys
        """
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, follow_redirects=True
            ) as client:
                response = await client.get(url)
                response.raise_for_status()

                # Only process HTML content
                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type:
                    return {"content": None, "title": None}

                html = response.text
                return self.extract_from_html(html, url)

        except httpx.HTTPError as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return {"content": None, "title": None}
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return {"content": None, "title": None}

    def extract_from_html(self, html: str, url: str = "") -> Dict[str, Optional[str]]:
        """
        Extract clean content from HTML string.

        Args:
            html: HTML content
            url: Original URL (for context)

        Returns:
            Dict with 'content' and 'title' keys
        """
        try:
            # Use readability to extract main content
            doc = Document(html)
            title = doc.title()
            clean_html = doc.summary()

            # Convert to text
            text_content = self.html_to_text.handle(clean_html)

            # Clean up the text
            text_content = self._clean_text(text_content)

            # Truncate if too long
            if len(text_content) > self.max_length:
                text_content = text_content[: self.max_length] + "..."

            return {"content": text_content, "title": title}

        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            # Fallback to basic extraction
            return self._basic_extraction(html)

    def _basic_extraction(self, html: str) -> Dict[str, Optional[str]]:
        """
        Basic fallback extraction using BeautifulSoup.

        Args:
            html: HTML content

        Returns:
            Dict with 'content' and 'title' keys
        """
        try:
            soup = BeautifulSoup(html, "lxml")

            # Extract title
            title_tag = soup.find("title")
            title = title_tag.get_text() if title_tag else None

            # Remove script and style elements
            for element in soup(["script", "style", "nav", "header", "footer"]):
                element.decompose()

            # Get text
            text = soup.get_text(separator="\n", strip=True)
            text = self._clean_text(text)

            if len(text) > self.max_length:
                text = text[: self.max_length] + "..."

            return {"content": text, "title": title}

        except Exception as e:
            logger.error(f"Basic extraction failed: {e}")
            return {"content": None, "title": None}

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split("\n")]
        lines = [line for line in lines if line]  # Remove empty lines

        # Join with single newline
        cleaned = "\n".join(lines)

        # Remove excessive consecutive newlines
        while "\n\n\n" in cleaned:
            cleaned = cleaned.replace("\n\n\n", "\n\n")

        return cleaned.strip()

    async def batch_extract(self, urls: list[str]) -> Dict[str, Dict[str, Optional[str]]]:
        """
        Extract content from multiple URLs concurrently.

        Args:
            urls: List of URLs to extract

        Returns:
            Dict mapping URLs to extracted content
        """
        tasks = [self.extract_from_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = {}
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to extract {url}: {result}")
                output[url] = {"content": None, "title": None}
            else:
                output[url] = result

        return output


# Global instance
content_extractor = ContentExtractor()
