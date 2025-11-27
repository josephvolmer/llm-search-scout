FROM python:3.11-slim

# OCI Standard Labels for License Compliance
LABEL org.opencontainers.image.title="LLM Search Scout"
LABEL org.opencontainers.image.description="Self-hosted search engine optimized for LLMs (contains AGPL-3.0 licensed SearXNG)"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.authors="Joseph Volmer"
LABEL org.opencontainers.image.url="https://github.com/josephvolmer/llm-search-scout"
LABEL org.opencontainers.image.source="https://github.com/josephvolmer/llm-search-scout"
LABEL org.opencontainers.image.licenses="MIT AND AGPL-3.0"
LABEL org.opencontainers.image.documentation="https://github.com/josephvolmer/llm-search-scout/blob/main/README.md"

# License-specific labels for transparency
LABEL com.llmsearchscout.component.api.license="MIT"
LABEL com.llmsearchscout.component.searxng.license="AGPL-3.0"
LABEL com.llmsearchscout.component.searxng.source="https://github.com/searxng/searxng"
LABEL com.llmsearchscout.component.searxng.path="/usr/local/searxng"
LABEL com.llmsearchscout.component.searxng.modified="false"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt1-dev \
    curl \
    wget \
    git \
    supervisor \
    build-essential \
    libffi-dev \
    libssl-dev \
    shellcheck \
    && rm -rf /var/lib/apt/lists/*

# Create directories
WORKDIR /usr/local/searxng
RUN mkdir -p /etc/searxng /var/log/searxng /app

# Install SearXNG from GitHub (AGPL-3.0 licensed - used unmodified)
# Source: https://github.com/searxng/searxng
# License: https://github.com/searxng/searxng/blob/master/LICENSE
RUN git clone https://github.com/searxng/searxng.git /usr/local/searxng && \
    cd /usr/local/searxng && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e .

# Copy SearXNG settings
COPY searxng/settings.yml /etc/searxng/settings.yml

# Install API dependencies
WORKDIR /app
COPY api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy API code
COPY api/ /app/

# Copy license and legal files for compliance
RUN mkdir -p /usr/local/share/licenses/llm-search-scout
COPY LICENSE /usr/local/share/licenses/llm-search-scout/LICENSE
COPY THIRD_PARTY_LICENSES /usr/local/share/licenses/llm-search-scout/THIRD_PARTY_LICENSES
COPY NOTICES.md /usr/local/share/licenses/llm-search-scout/NOTICES.md

# Create supervisor config to run both services
RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /etc/searxng && \
    chown -R appuser:appuser /var/log/searxng && \
    chown -R appuser:appuser /usr/local/searxng

# Expose API port (SearXNG runs internally on 8080)
EXPOSE 8000

# Health check on the API
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run both services via supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
