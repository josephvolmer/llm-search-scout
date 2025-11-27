"""Citation formatting service for generating academic citations."""

from typing import Dict, Optional
from datetime import datetime
from urllib.parse import urlparse
import re
import logging

logger = logging.getLogger(__name__)


class CitationFormatter:
    """Format citations in common academic styles."""

    def format_citations(
        self,
        title: str,
        url: str,
        source: str,
        published_date: Optional[str] = None,
        author: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Generate citations in multiple formats.

        Args:
            title: Page/article title
            url: Source URL
            source: Domain name
            published_date: Publication date (ISO 8601)
            author: Author name (if known)

        Returns:
            Dict with APA, MLA, and Chicago style citations
        """
        # Extract year from date
        year = None
        if published_date:
            try:
                year = published_date.split("-")[0]
            except Exception:
                pass

        # Use current year if no date available
        if not year:
            year = str(datetime.utcnow().year)

        # Clean title
        title = self._clean_title(title)

        # Generate author (use source domain if not provided)
        if not author:
            author = self._generate_author_from_source(source)

        return {
            "apa": self._format_apa(title, url, source, year, author, published_date),
            "mla": self._format_mla(title, url, source, year, author),
            "chicago": self._format_chicago(title, url, source, year, author),
        }

    def _clean_title(self, title: str) -> str:
        """
        Clean and normalize title.

        Args:
            title: Raw title

        Returns:
            Cleaned title
        """
        # Remove common suffixes
        suffixes_to_remove = [
            r"\s*-\s*[^-]+$",  # " - Site Name" at end
            r"\s*\|\s*[^|]+$",  # " | Site Name" at end
        ]

        for pattern in suffixes_to_remove:
            title = re.sub(pattern, "", title)

        # Ensure title ends with period for citations (if not already punctuated)
        if title and not title[-1] in ".!?":
            title += "."

        return title.strip()

    def _generate_author_from_source(self, source: str) -> str:
        """
        Generate author name from source domain.

        Args:
            source: Domain name

        Returns:
            Author string
        """
        # Remove TLD
        parts = source.split(".")
        if len(parts) > 1:
            name = parts[-2]
        else:
            name = source

        # Capitalize
        name = name.capitalize()

        # Handle special cases
        special_cases = {
            "nytimes": "The New York Times",
            "bbc": "BBC",
            "github": "GitHub",
            "stackoverflow": "Stack Overflow",
            "wikipedia": "Wikipedia",
            "arxiv": "arXiv",
            "pubmed": "PubMed",
        }

        for key, value in special_cases.items():
            if key in source.lower():
                return value

        return name

    def _format_apa(
        self,
        title: str,
        url: str,
        source: str,
        year: str,
        author: str,
        published_date: Optional[str],
    ) -> str:
        """
        Format citation in APA style.

        APA 7th edition web format:
        Author. (Year, Month Day). Title. Source. URL

        Args:
            title: Title
            url: URL
            source: Source domain
            year: Publication year
            author: Author
            published_date: Full date if available

        Returns:
            APA formatted citation
        """
        # Format date
        if published_date:
            try:
                # Parse ISO date to "Month Day"
                parts = published_date.split("-")
                if len(parts) == 3:
                    dt = datetime.strptime(published_date, "%Y-%m-%d")
                    month_day = dt.strftime("%B %d")
                    date_str = f"{year}, {month_day}"
                else:
                    date_str = year
            except Exception:
                date_str = year
        else:
            date_str = year

        return f"{author}. ({date_str}). {title} {source}. {url}"

    def _format_mla(
        self, title: str, url: str, source: str, year: str, author: str
    ) -> str:
        """
        Format citation in MLA style.

        MLA 9th edition web format:
        Author. "Title." Source, Year, URL.

        Args:
            title: Title
            url: URL
            source: Source domain
            year: Publication year
            author: Author

        Returns:
            MLA formatted citation
        """
        # MLA uses quotes around article titles
        if not title.startswith('"'):
            title = f'"{title[:-1]}"' if title.endswith(".") else f'"{title}"'

        return f'{author}. {title} {source}, {year}, {url}.'

    def _format_chicago(
        self, title: str, url: str, source: str, year: str, author: str
    ) -> str:
        """
        Format citation in Chicago style.

        Chicago 17th edition web format:
        Author. "Title." Source. Year. URL.

        Args:
            title: Title
            url: URL
            source: Source domain
            year: Publication year
            author: Author

        Returns:
            Chicago formatted citation
        """
        # Chicago uses quotes around article titles
        if not title.startswith('"'):
            title = f'"{title[:-1]}"' if title.endswith(".") else f'"{title}"'

        return f'{author}. {title} {source}. {year}. {url}.'


# Global instance
citation_formatter = CitationFormatter()
