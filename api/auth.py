"""API key authentication and rate limiting."""

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
import asyncio

from config import settings

# API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Rate limiting storage: {api_key: [(timestamp1, timestamp2, ...)]}
_rate_limit_store: Dict[str, list] = defaultdict(list)
_rate_limit_lock = asyncio.Lock()


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify that the provided API key is valid.

    Args:
        api_key: The API key from the X-API-Key header

    Returns:
        The validated API key

    Raises:
        HTTPException: 401 if key is missing, 403 if invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    valid_keys = settings.api_keys_list

    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    return api_key


async def check_rate_limit(api_key: str) -> Tuple[int, int, datetime]:
    """
    Check if the API key has exceeded rate limits.

    Args:
        api_key: The validated API key

    Returns:
        Tuple of (remaining_requests, limit, reset_time)

    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    async with _rate_limit_lock:
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=1)

        # Get request timestamps for this key
        timestamps = _rate_limit_store[api_key]

        # Remove old timestamps outside the current window
        timestamps[:] = [ts for ts in timestamps if ts > window_start]

        # Check if limit exceeded
        current_count = len(timestamps)
        limit = settings.rate_limit_per_minute

        if current_count >= limit:
            # Calculate when the oldest request will expire
            oldest_request = min(timestamps)
            reset_time = oldest_request + timedelta(minutes=1)
            seconds_until_reset = int((reset_time - now).total_seconds())

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {seconds_until_reset} seconds.",
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_time.timestamp())),
                    "Retry-After": str(seconds_until_reset),
                },
            )

        # Add current request timestamp
        timestamps.append(now)

        # Calculate remaining requests and reset time
        remaining = limit - len(timestamps)
        reset_time = now + timedelta(minutes=1)

        return remaining, limit, reset_time


async def verify_api_key_with_rate_limit(
    api_key: str = Security(api_key_header),
) -> Tuple[str, Dict[str, str]]:
    """
    Verify API key and check rate limits in one step.

    Args:
        api_key: The API key from the X-API-Key header

    Returns:
        Tuple of (api_key, rate_limit_headers)

    Raises:
        HTTPException: For auth or rate limit violations
    """
    # Verify the API key is valid
    validated_key = await verify_api_key(api_key)

    # Check rate limits
    remaining, limit, reset_time = await check_rate_limit(validated_key)

    # Prepare rate limit headers
    headers = {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset": str(int(reset_time.timestamp())),
    }

    return validated_key, headers


async def cleanup_old_rate_limit_data():
    """
    Periodic cleanup task to remove old rate limit data.
    Should be run as a background task.
    """
    while True:
        await asyncio.sleep(300)  # Run every 5 minutes

        async with _rate_limit_lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(minutes=5)

            # Clean up old entries
            for key in list(_rate_limit_store.keys()):
                timestamps = _rate_limit_store[key]
                timestamps[:] = [ts for ts in timestamps if ts > cutoff]

                # Remove empty entries
                if not timestamps:
                    del _rate_limit_store[key]
