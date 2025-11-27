FROM python:3.11-slim

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

# Install SearXNG from GitHub (use master branch - most stable)
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
