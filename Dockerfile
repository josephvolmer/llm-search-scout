###############################################################################
# Stage 1: Builder - Install dependencies and build SearXNG
###############################################################################
FROM python:3.11-alpine AS builder

# Install build dependencies (Alpine packages)
RUN apk add --no-cache \
    gcc \
    g++ \
    musl-dev \
    libxml2-dev \
    libxslt-dev \
    git \
    make \
    libffi-dev \
    openssl-dev \
    linux-headers

# Clone and install SearXNG (AGPL-3.0 licensed - used unmodified)
# Source: https://github.com/searxng/searxng
# License: https://github.com/searxng/searxng/blob/master/LICENSE
RUN git clone --depth 1 https://github.com/searxng/searxng.git /usr/local/searxng && \
    cd /usr/local/searxng && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir . && \
    # Remove unnecessary files to save space
    rm -rf /usr/local/searxng/.git \
           /usr/local/searxng/tests \
           /usr/local/searxng/docs \
           /usr/local/searxng/.github \
           /usr/local/searxng/utils/standalone_searx.py \
           /usr/local/searxng/*.md

# Install API dependencies
COPY api/requirements.txt /tmp/api-requirements.txt
RUN pip install --no-cache-dir -r /tmp/api-requirements.txt && \
    # Remove pip, setuptools, and wheel to save space (not needed at runtime)
    pip uninstall -y pip setuptools wheel && \
    # Remove Python cache files
    find /usr/local/lib/python3.11 -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.11 -type f -name '*.pyc' -delete && \
    find /usr/local/lib/python3.11 -type f -name '*.pyo' -delete && \
    # Remove test files from packages
    find /usr/local/lib/python3.11/site-packages -type d -name tests -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.11/site-packages -type d -name test -exec rm -rf {} + 2>/dev/null || true

###############################################################################
# Stage 2: Runtime - Minimal Alpine runtime image
###############################################################################
FROM python:3.11-alpine

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

# Install ONLY runtime dependencies (Alpine packages)
RUN apk add --no-cache \
    libxml2 \
    libxslt \
    curl \
    git \
    supervisor

# Create non-root user first (before copying files)
RUN adduser -D -u 1000 appuser

# Create directories with correct ownership
RUN mkdir -p /usr/local/searxng /etc/searxng /var/log/searxng /app /var/log/supervisor && \
    chown -R appuser:appuser /usr/local/searxng /etc/searxng /var/log/searxng /app /var/log/supervisor

# Copy Python packages from builder (pip already removed in builder)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy SearXNG from builder (without .git, tests, docs)
COPY --from=builder --chown=appuser:appuser /usr/local/searxng /usr/local/searxng

# Final cleanup: remove any remaining caches and unnecessary files
RUN find /usr/local -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local -type f -name '*.pyc' -delete && \
    find /usr/local -type f -name '*.pyo' -delete && \
    rm -rf /root/.cache /tmp/* /var/cache/apk/*

# Copy SearXNG settings
COPY --chown=appuser:appuser searxng/settings.yml /etc/searxng/settings.yml

# Copy API code
WORKDIR /app
COPY --chown=appuser:appuser api/ /app/

# Copy license and legal files for compliance
RUN mkdir -p /usr/local/share/licenses/llm-search-scout
COPY LICENSE /usr/local/share/licenses/llm-search-scout/LICENSE
COPY THIRD_PARTY_LICENSES /usr/local/share/licenses/llm-search-scout/THIRD_PARTY_LICENSES
COPY NOTICES.md /usr/local/share/licenses/llm-search-scout/NOTICES.md

# Copy supervisor config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose API port (SearXNG runs internally on 8080)
EXPOSE 8000

# Health check on the API
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run both services via supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
