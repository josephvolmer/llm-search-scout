#!/bin/bash

# LLM Search Scout Quick Start Script

set -e

echo "======================================"
echo "LLM Search Scout - Quick Start"
echo "======================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Generate API key if .env doesn't exist or has default key
if [ ! -f .env ] || grep -q "demo-key-change-this-in-production" .env; then
    echo "Generating secure API key..."
    NEW_API_KEY=$(openssl rand -hex 32)

    if [ -f .env ]; then
        # Replace the demo key with new one
        sed -i.bak "s/API_KEYS=.*/API_KEYS=$NEW_API_KEY/" .env
        rm .env.bak 2>/dev/null || true
    else
        # Create .env from example
        cp .env.example .env
        sed -i.bak "s/API_KEYS=.*/API_KEYS=$NEW_API_KEY/" .env
        rm .env.bak 2>/dev/null || true
    fi

    echo "Generated new API key: $NEW_API_KEY"
    echo "Saved to .env file"
    echo ""
fi

# Generate SearXNG secret key if needed
if grep -q "change-this-to-a-random-secret-key" .env; then
    echo "Generating SearXNG secret key..."
    SEARXNG_SECRET=$(openssl rand -hex 32)
    sed -i.bak "s/SEARXNG_SECRET_KEY=.*/SEARXNG_SECRET_KEY=$SEARXNG_SECRET/" .env
    rm .env.bak 2>/dev/null || true
fi

echo "Starting services..."
echo ""

# Start Docker Compose
docker-compose up -d

echo ""
echo "======================================"
echo "Services are starting up!"
echo "======================================"
echo ""
echo "This may take 30-60 seconds for first time setup."
echo ""
echo "API will be available at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "To check status:"
echo "  docker-compose ps"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To test the API:"
echo "  curl -H \"X-API-Key: $(grep API_KEYS .env | cut -d= -f2 | cut -d, -f1)\" \\"
echo "    \"http://localhost:8000/health\""
echo ""
echo "Your API Key:"
echo "  $(grep API_KEYS .env | cut -d= -f2 | cut -d, -f1)"
echo ""
echo "======================================"
