"""Metadata enrichment service for adding context to search results."""

import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
from datetime import datetime
from dateutil import parser as date_parser
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class MetadataEnricher:
    """Enrich search results with metadata."""

    # Known high-quality domains and their credibility scores
    CREDIBILITY_SCORES = {
        # Academic & Research
        "arxiv.org": 0.95,
        "scholar.google.com": 0.95,
        "pubmed.ncbi.nlm.nih.gov": 0.95,
        "semanticscholar.org": 0.9,
        "jstor.org": 0.9,
        "researchgate.net": 0.85,
        # Documentation & Official
        "github.com": 0.9,
        "stackoverflow.com": 0.85,
        "developer.mozilla.org": 0.95,
        "docs.python.org": 0.95,
        "docs.microsoft.com": 0.9,
        # News & Media
        "reuters.com": 0.9,
        "apnews.com": 0.9,
        "bbc.com": 0.85,
        "nytimes.com": 0.85,
        "theguardian.com": 0.85,
        # Reference
        "wikipedia.org": 0.8,
        "britannica.com": 0.85,
        # Tech & Industry
        "techcrunch.com": 0.75,
        "arstechnica.com": 0.8,
        "wired.com": 0.75,
    }

    # Content type patterns
    CONTENT_TYPE_PATTERNS = {
        "article": r"/(article|post|blog|news)/",
        "documentation": r"/(docs|documentation|reference|api|guide)/",
        "forum": r"/(forum|discussion|thread|questions)/",
        "tutorial": r"/(tutorial|how-to|guide|learn)/",
        "video": r"/(watch|video)/",
        "pdf": r"\.pdf$",
        "wiki": r"/(wiki|encyclopedia)/",
    }

    def enrich(
        self, result: Dict[str, Any], original_content: str = ""
    ) -> Dict[str, Any]:
        """
        Enrich a search result with metadata.

        Args:
            result: Raw search result from SearXNG
            original_content: Full extracted content (for word count)

        Returns:
            Dict with metadata fields
        """
        url = result.get("url", "")
        content = result.get("content", "")
        title = result.get("title", "")
        snippet = result.get("snippet", "")

        # Combine all text for analysis
        full_text = original_content or content

        metadata = {
            "published_date": self._extract_date(result, url, title),
            "source": self._extract_source(url),
            "content_type": self._detect_content_type(url),
            "word_count": self._count_words(full_text),
            "credibility_score": self._calculate_credibility(url, result),
            "language": self._detect_language(full_text),
            "reading_time_minutes": self._calculate_reading_time(full_text),
            "keywords": self._extract_keywords(full_text, title),
            "is_direct_answer": self._detect_direct_answer(snippet, content, title),
        }

        return metadata

    def _extract_date(self, result: Dict[str, Any], url: str = "", title: str = "") -> Optional[str]:
        """
        Extract publication date from result, URL, or title.

        Args:
            result: Search result
            url: URL to extract from
            title: Title to extract from

        Returns:
            ISO 8601 date string or None
        """
        # Check if SearXNG provided a publishedDate
        if "publishedDate" in result and result["publishedDate"]:
            try:
                # Parse datetime and convert to ISO 8601 date only
                dt = date_parser.parse(str(result["publishedDate"]))
                return dt.date().isoformat()
            except Exception as e:
                logger.debug(f"Failed to parse publishedDate: {e}")

        # Try to extract from URL first (often most reliable)
        # Common URL patterns: /2024/01/15/, /2024-01-15/, ?date=2024-01-15
        url_date_patterns = [
            r"/(\d{4})/(\d{2})/(\d{2})/",  # /2024/01/15/
            r"/(\d{4})-(\d{2})-(\d{2})",    # /2024-01-15
            r"[?&]date=(\d{4}-\d{2}-\d{2})",  # ?date=2024-01-15
        ]

        for pattern in url_date_patterns:
            match = re.search(pattern, url)
            if match:
                try:
                    if len(match.groups()) == 3:
                        year, month, day = match.groups()
                        return f"{year}-{month}-{day}"
                    else:
                        dt = date_parser.parse(match.group(1))
                        return dt.date().isoformat()
                except Exception:
                    continue

        # Try to extract from title and content
        content = result.get("content", "") + " " + title

        # Common date patterns
        date_patterns = [
            r"\b(\d{4})-(\d{2})-(\d{2})\b",  # 2024-01-15
            r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{1,2}),? (\d{4})\b",  # Jan 15, 2024
            r"\b(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{4})\b",  # 15 Jan 2024
            r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",  # 01/15/2024
        ]

        for pattern in date_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group(0)
                    dt = date_parser.parse(date_str, fuzzy=True)
                    # Only return dates that seem reasonable (not too far in future)
                    if dt.year <= datetime.now().year + 1:
                        return dt.date().isoformat()
                except Exception:
                    continue

        return None

    def _extract_source(self, url: str) -> str:
        """
        Extract source domain from URL.

        Args:
            url: Full URL

        Returns:
            Domain name
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc

            # Remove www. prefix
            if domain.startswith("www."):
                domain = domain[4:]

            return domain
        except Exception:
            return "unknown"

    def _detect_content_type(self, url: str) -> str:
        """
        Detect content type from URL patterns.

        Args:
            url: Full URL

        Returns:
            Content type string
        """
        url_lower = url.lower()

        for content_type, pattern in self.CONTENT_TYPE_PATTERNS.items():
            if re.search(pattern, url_lower):
                return content_type

        # Check domain for specific types
        if "github.com" in url_lower:
            return "code"
        elif "youtube.com" in url_lower or "youtu.be" in url_lower:
            return "video"
        elif "stackoverflow.com" in url_lower:
            return "forum"
        elif "wikipedia.org" in url_lower:
            return "encyclopedia"

        return "webpage"

    def _count_words(self, text: str) -> Optional[int]:
        """
        Count words in text.

        Args:
            text: Text content

        Returns:
            Word count or None
        """
        if not text:
            return None

        # Simple word count (split by whitespace)
        words = text.split()
        return len(words)

    def _calculate_credibility(
        self, url: str, result: Dict[str, Any]
    ) -> Optional[float]:
        """
        Calculate credibility score for a source.

        Args:
            url: Source URL
            result: Search result

        Returns:
            Credibility score 0-1 or None
        """
        source = self._extract_source(url)

        # Check if we have a predefined score
        if source in self.CREDIBILITY_SCORES:
            return self.CREDIBILITY_SCORES[source]

        # Calculate heuristic score
        score = 0.5  # Base score

        # HTTPS bonus
        if url.startswith("https://"):
            score += 0.1

        # Domain characteristics
        if ".edu" in source:
            score += 0.2
        elif ".gov" in source:
            score += 0.25
        elif ".org" in source:
            score += 0.1

        # Penalize certain patterns
        if any(keyword in source for keyword in ["blog", "forum", "wiki"]):
            score -= 0.1

        # Clamp to 0-1 range
        return max(0.0, min(1.0, score))

    def _detect_language(self, text: str) -> Optional[str]:
        """
        Detect language of text using simple heuristics.

        Args:
            text: Text content

        Returns:
            Language code or None
        """
        if not text or len(text) < 20:
            return None

        # Simple language detection based on common words
        text_lower = text.lower()

        # English indicators
        english_words = ['the', 'and', 'for', 'that', 'with', 'this', 'from', 'are', 'was']
        english_count = sum(1 for word in english_words if f' {word} ' in text_lower)

        # Spanish indicators
        spanish_words = ['el', 'la', 'de', 'que', 'en', 'los', 'del', 'para', 'con']
        spanish_count = sum(1 for word in spanish_words if f' {word} ' in text_lower)

        # French indicators
        french_words = ['le', 'de', 'un', 'et', 'à', 'dans', 'les', 'des', 'pour']
        french_count = sum(1 for word in french_words if f' {word} ' in text_lower)

        # German indicators
        german_words = ['der', 'die', 'das', 'und', 'den', 'ist', 'für', 'von', 'mit']
        german_count = sum(1 for word in german_words if f' {word} ' in text_lower)

        # Determine language (simple majority vote)
        counts = {
            'en': english_count,
            'es': spanish_count,
            'fr': french_count,
            'de': german_count
        }

        max_count = max(counts.values())
        if max_count >= 2:  # At least 2 matches
            return max(counts, key=counts.get)

        return 'en'  # Default to English

    def _calculate_reading_time(self, text: str) -> Optional[int]:
        """
        Calculate estimated reading time in minutes.

        Args:
            text: Text content

        Returns:
            Reading time in minutes or None
        """
        if not text:
            return None

        word_count = self._count_words(text)
        if not word_count:
            return None

        # Average reading speed: 200-250 words per minute
        # Using 225 as middle ground
        reading_time = max(1, round(word_count / 225))

        return reading_time

    def _extract_keywords(self, text: str, title: str = "") -> Optional[List[str]]:
        """
        Extract top keywords from text.

        Args:
            text: Text content
            title: Title (weighted more heavily)

        Returns:
            List of top keywords or None
        """
        if not text or len(text) < 20:
            return None

        # Combine title (weighted 3x) and text
        combined_text = (title + " ") * 3 + text

        # Convert to lowercase and extract words
        words = re.findall(r'\b[a-z]{3,}\b', combined_text.lower())

        # Common stop words to filter out
        stop_words = {
            'the', 'and', 'for', 'that', 'with', 'this', 'from', 'are', 'was',
            'but', 'not', 'you', 'all', 'can', 'her', 'has', 'had', 'our',
            'out', 'one', 'two', 'more', 'than', 'been', 'have', 'will',
            'what', 'when', 'who', 'which', 'their', 'said', 'each', 'about',
            'how', 'other', 'into', 'after', 'also', 'some', 'these', 'only',
            'then', 'now', 'may', 'such', 'very', 'over', 'just', 'where',
            'most', 'both', 'through', 'way', 'could', 'before', 'does'
        }

        # Filter stop words and count frequencies
        filtered_words = [w for w in words if w not in stop_words]

        if not filtered_words:
            return None

        # Get top keywords by frequency
        word_counts = Counter(filtered_words)
        top_keywords = [word for word, _ in word_counts.most_common(10)]

        return top_keywords[:10] if top_keywords else None

    def _detect_direct_answer(self, snippet: str, content: str, title: str) -> bool:
        """
        Detect if this result appears to be a direct answer.

        Args:
            snippet: Short snippet from search engine
            content: Full content
            title: Title

        Returns:
            True if appears to be a direct answer
        """
        # Check snippet and content for direct answer patterns
        text = (snippet + " " + content[:200]).lower()

        # Direct answer indicators
        direct_answer_patterns = [
            r'^(yes|no)[,\.]',  # Starts with yes/no
            r'^\d+',  # Starts with a number
            r'(is|are|was|were)\s+\w+',  # Definition patterns
            r'means\s+\w+',  # "X means..."
            r'refers to',  # "X refers to..."
            r'^the answer is',
            r'^in short',
            r'^simply put',
            r'definition[:]\s*',
        ]

        for pattern in direct_answer_patterns:
            if re.search(pattern, text):
                return True

        # Check if title is a question and content starts with answer
        if '?' in title and any(content.strip().lower().startswith(word) for word in ['yes', 'no', 'the', 'it']):
            return True

        return False


# Global instance
metadata_enricher = MetadataEnricher()
