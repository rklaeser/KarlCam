#!/bin/bash

# Script to fix Gemini model naming issue in production
# This updates the labeler_config table to use the correct model names

set -e

echo "==================================="
echo "Gemini Model Name Fix for Production"
echo "==================================="
echo ""
echo "This script will update the Gemini model names in the production database"
echo "from 'gemini-1.5-flash' to 'gemini-1.5-flash-latest'"
echo ""

# Check if we're running the Cloud SQL proxy
if ! lsof -i :5432 > /dev/null 2>&1; then
    echo "❌ Cloud SQL proxy is not running on port 5432"
    echo "Please run: make start-sql"
    exit 1
fi

echo "✅ Cloud SQL proxy is running"

# Get database password from environment or secrets
if [ -z "$KARLCAM_DB_PASSWORD" ]; then
    echo "Getting database password from secrets..."
    export KARLCAM_DB_PASSWORD=$(gcloud secrets versions access latest --secret="karlcam-db-password" --project=karlcam 2>/dev/null)
    
    if [ -z "$KARLCAM_DB_PASSWORD" ]; then
        echo "❌ Failed to get database password"
        echo "Please set KARLCAM_DB_PASSWORD environment variable or ensure you have access to the secret"
        exit 1
    fi
fi

# Production database connection
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="karlcam_production"
DB_USER="karlcam_production"

echo ""
echo "Connecting to production database..."
echo ""

# Apply the migration
echo "Applying migration to fix model names..."
psql "postgresql://${DB_USER}:${KARLCAM_DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}" < db/migrations/002_update_gemini_model_names.sql

echo ""
echo "==================================="
echo "✅ Migration completed successfully!"
echo "==================================="
echo ""
echo "The Gemini model names have been updated in the production database."
echo "The next collection run should work without errors."
echo ""
echo "To verify the fix:"
echo "1. Check the next scheduled run logs"
echo "2. Or manually trigger a collection: gcloud run jobs execute karlcam-collector-production --region=us-central1"