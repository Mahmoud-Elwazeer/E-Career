#!/bin/bash
# Setup Qdrant Vector Database
# Run this script on the production server to start Qdrant

set -e

echo "=== Qdrant Vector Database Setup ==="
echo ""

# Check if Docker is running
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed or not running"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: docker-compose is not installed"
    exit 1
fi

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Project root: $PROJECT_ROOT"
echo ""

# Navigate to project root
cd "$PROJECT_ROOT"

# Start Qdrant using docker-compose
echo "Starting Qdrant container..."
docker-compose -f docker-compose.qdrant.yml up -d

# Wait for Qdrant to be ready
echo "Waiting for Qdrant to be ready..."
sleep 10

# Check if Qdrant is healthy
echo "Checking Qdrant health..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:6333 || echo "000")

if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo "✓ Qdrant is running and healthy!"
    echo ""
    echo "=== Qdrant Information ==="
    echo "URL: http://localhost:6333"
    echo "API Port: 6334"
    echo "Storage: qdrant_data volume"
    echo ""
    echo "=== Next Steps ==="
    echo "1. Index jobs: cd backend && python manage.py index_jobs"
    echo "2. Test the API: curl http://localhost:6333/collections"
    echo ""
else
    echo "⚠ Qdrant may not be fully ready yet. Health check returned: $HEALTH_RESPONSE"
    echo "Please wait a few more seconds and try again."
    echo ""
    echo "To check status manually:"
    echo "  docker-compose -f docker-compose.qdrant.yml ps"
    echo "  docker-compose -f docker-compose.qdrant.yml logs"
fi

# Show container status
echo ""
echo "=== Container Status ==="
docker-compose -f docker-compose.qdrant.yml ps