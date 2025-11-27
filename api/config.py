"""Configuration management using Pydantic settings."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    api_keys: str = "default-insecure-key"  # Comma-separated list
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "info"

    # SearXNG Configuration
    searxng_url: str = "http://searxng:8080"

    # Search Configuration
    max_results: int = 50
    default_results: int = 10
    rate_limit_per_minute: int = 60

    # Content Extraction
    max_content_length: int = 5000
    extract_timeout_seconds: int = 10

    # AI Features (optional)
    openai_api_key: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def api_keys_list(self) -> List[str]:
        """Parse comma-separated API keys into a list."""
        return [key.strip() for key in self.api_keys.split(",") if key.strip()]

    @property
    def has_openai(self) -> bool:
        """Check if OpenAI API key is configured."""
        return bool(self.openai_api_key and self.openai_api_key.strip())


# Global settings instance
settings = Settings()
