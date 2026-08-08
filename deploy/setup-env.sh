#!/bin/bash
# Setup Environment Variables for USAM Career Compass
# This script helps set up the production environment

set -e

echo "=== USAM Career Compass Environment Setup ==="
echo ""

# Check if running on production server
if [ ! -f "/var/www/usam/backend/.env" ]; then
    echo "Error: .env file not found at /var/www/usam/backend/.env"
    echo "Please create the .env file first by copying .env.example"
    exit 1
fi

# Backup current .env
echo "Creating backup of .env file..."
cp /var/www/usam/backend/.env /var/www/usam/backend/.env.backup.$(date +%Y%m%d_%H%M%S)

echo ""
echo "=== Environment Variables to Configure ==="
echo ""

# Typesense Configuration
echo "1. Typesense Configuration:"
echo "   - TYPESENSE_HOST: Your Typesense server hostname"
echo "   - TYPESENSE_PORT: Your Typesense server port (default: 8108)"
echo "   - TYPESENSE_PROTOCOL: http or https"
echo "   - TYPESENSE_API_KEY: Your Typesense API key"
echo ""

# Qdrant Configuration
echo "2. Qdrant Configuration:"
echo "   - QDRANT_HOST: Your Qdrant server hostname"
echo "   - QDRANT_PORT: Your Qdrant server port (default: 6333)"
echo "   - QDRANT_API_KEY: Your Qdrant API key"
echo ""

# Read current values
echo "Current .env values:"
grep -E "^(TYPESENSE_|QDRANT_)" /var/www/usam/backend/.env 2>/dev/null || echo "  (not set)"

echo ""
echo "=== Instructions ==="
echo ""
echo "Edit the .env file to add/update these variables:"
echo "  sudo nano /var/www/usam/backend/.env"
echo ""
echo "Or use sed to update specific values:"
echo "  sudo sed -i 's/^TYPESENSE_API_KEY=.*/TYPESENSE_API_KEY=your-key/' /var/www/usam/backend/.env"
echo "  sudo sed -i 's/^QDRANT_API_KEY=.*/QDRANT_API_KEY=your-key/' /var/www/usam/backend/.env"
echo ""
echo "After updating, restart the service:"
echo "  sudo systemctl restart usam.service"
echo ""
echo "Verify the service is running:"
echo "  sudo systemctl status usam.service"
echo ""