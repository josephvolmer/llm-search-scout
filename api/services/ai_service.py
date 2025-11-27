"""AI-powered features using OpenAI API."""

import logging
from typing import List, Optional
from openai import AsyncOpenAI
import numpy as np

from config import settings

logger = logging.getLogger(__name__)


class AIService:
    """AI service for summarization, embeddings, and deduplication."""

    def __init__(self):
        """Initialize AI service."""
        self.client = None
        if settings.has_openai:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            logger.info("OpenAI client initialized")
        else:
            logger.info("OpenAI API key not configured, AI features disabled")

    async def summarize_content(self, content: str, title: str) -> Optional[str]:
        """
        Generate AI summary of content.

        Args:
            content: Full text content
            title: Page title

        Returns:
            Summary string or None if fails
        """
        if not self.client:
            logger.warning("OpenAI client not initialized")
            return None

        try:
            # Truncate content to reasonable length (avoid token limits)
            max_chars = 3000
            truncated_content = content[:max_chars]
            if len(content) > max_chars:
                truncated_content += "..."

            prompt = f"""Summarize the following article in 2-3 concise sentences. Focus on the main points and key takeaways.

Title: {title}

Content:
{truncated_content}

Summary:"""

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that creates concise, accurate summaries of articles and web content.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=150,
                temperature=0.3,
            )

            summary = response.choices[0].message.content.strip()
            logger.debug(f"Generated summary for: {title[:50]}...")
            return summary

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return None

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate vector embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector or None if fails
        """
        if not self.client:
            logger.warning("OpenAI client not initialized")
            return None

        try:
            # Truncate to reasonable length
            max_chars = 8000
            truncated_text = text[:max_chars]

            response = await self.client.embeddings.create(
                model="text-embedding-3-small", input=truncated_text
            )

            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding with dimension: {len(embedding)}")
            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None

    async def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate vector embeddings for multiple texts in a single API call.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors (or None for failed embeddings)
        """
        if not self.client:
            logger.warning("OpenAI client not initialized")
            return [None] * len(texts)

        if not texts:
            return []

        try:
            # Truncate all texts to reasonable length
            max_chars = 8000
            truncated_texts = [text[:max_chars] for text in texts]

            # OpenAI supports batch embeddings (up to 2048 inputs)
            # Process in batches of 100 to be safe
            batch_size = 100
            all_embeddings = []

            for i in range(0, len(truncated_texts), batch_size):
                batch = truncated_texts[i:i + batch_size]

                response = await self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=batch
                )

                # Extract embeddings in order
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

            logger.info(f"Generated {len(all_embeddings)} embeddings in batch")
            return all_embeddings

        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return [None] * len(texts)

    def cosine_similarity(
        self, vec1: List[float], vec2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Similarity score 0-1
        """
        try:
            a = np.array(vec1)
            b = np.array(vec2)

            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)

            if norm_a == 0 or norm_b == 0:
                return 0.0

            return float(dot_product / (norm_a * norm_b))

        except Exception as e:
            logger.error(f"Failed to calculate cosine similarity: {e}")
            return 0.0

    def deduplicate_by_embeddings(
        self, results_with_embeddings: List[tuple], threshold: float = 0.95
    ) -> List[int]:
        """
        Identify duplicate results using embedding similarity.

        Args:
            results_with_embeddings: List of (index, embedding) tuples
            threshold: Similarity threshold for duplicates (0.95 = 95% similar)

        Returns:
            List of indices to keep (duplicates removed)
        """
        if not results_with_embeddings:
            return []

        # Track which indices to keep
        keep_indices = []
        seen_embeddings = []

        for idx, embedding in results_with_embeddings:
            if embedding is None:
                # Keep results without embeddings
                keep_indices.append(idx)
                continue

            # Check similarity with all previously seen embeddings
            is_duplicate = False
            for seen_emb in seen_embeddings:
                similarity = self.cosine_similarity(embedding, seen_emb)
                if similarity >= threshold:
                    logger.debug(f"Found duplicate result (similarity: {similarity:.3f})")
                    is_duplicate = True
                    break

            if not is_duplicate:
                keep_indices.append(idx)
                seen_embeddings.append(embedding)

        logger.info(
            f"Deduplication: kept {len(keep_indices)}/{len(results_with_embeddings)} results"
        )
        return keep_indices


# Global instance
ai_service = AIService()
