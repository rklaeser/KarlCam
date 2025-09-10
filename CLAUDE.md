# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KarlCam is a serverless webcam monitoring system built on Google Cloud Platform that collects images from webcams across San Francisco, analyzes them for fog conditions using AI, and provides public and admin interfaces to view the data.

## Architecture

### Core Components
- **Data Collection Service** (`collect/`): Cloud Run Job that periodically fetches webcam images and stores them in Cloud Storage
- **Labeling Service** (`label/`): Uses Gemini AI to analyze images for fog conditions
- **API Backend** (`web/api/`): FastAPI service providing REST endpoints for public data access
- **Public Frontend** (`web/frontend/`): React application for viewing webcam data and fog conditions
- **Admin System** (`admin/`): Management interface for system administration
- **Database** (`db/`): PostgreSQL models and schema management

### Data Flow
1. Collector fetches images from webcams → stores in Cloud Storage + metadata in PostgreSQL
2. Labeler processes images → adds fog analysis labels to PostgreSQL
3. API serves labeled data → consumed by frontend applications

### Database Schema
- `webcams`: Camera configurations and metadata
- `collection_runs`: Tracking of collection job executions
- `image_collections`: Raw collected images metadata
- `image_labels`: AI-generated labels for fog analysis (supports multiple labelers)
- `system_status`: System state tracking

## Development Commands

### Local Development Setup

```bash
# Start Cloud SQL Proxy (required for local development)
make start-sql

# Get database password
gcloud secrets versions access latest --secret="karlcam-db-password" --project=karlcam

# Start individual services
make start-api            # API server on http://localhost:8002
make start-frontend       # Frontend on http://localhost:3000
make start-admin-backend  # Admin API on http://localhost:8001
make start-admin-frontend # Admin UI on http://localhost:3001
make start-collect        # Run collector locally
```

### Python Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies for specific service
pip install -r web/api/requirements.txt
pip install -r collect/requirements.txt
pip install -r label/requirements.txt

# Initialize database
python -m db.init_db
```

### Frontend Development

```bash
# Web frontend
cd web/frontend
npm install
npm start         # Development server
npm run build     # Production build
npm test          # Run tests

# Admin frontend
cd admin/frontend
npm install
npm start
npm run build
```

### Deployment

```bash
# Deploy via Cloud Build (automatic on push to main)
gcloud builds submit --config=cloudbuild.yaml

# Manual deployment of individual services
gcloud run deploy karlcam-api-v2 --image gcr.io/karlcam/karlcam-api:latest --region us-central1
gcloud run jobs update karlcam-collector-v2 --image gcr.io/karlcam/karlcam-collector:latest --region us-central1

# Execute collector job manually
gcloud run jobs execute karlcam-collector-v2 --region=us-central1
```

### Infrastructure Management

```bash
# Terraform deployment (from terraform/ directory)
terraform init -backend-config="bucket=karlcam-terraform-state" -backend-config="prefix=terraform/state/staging"
terraform plan
terraform apply

# View service logs
gcloud run logs read karlcam-api-v2 --region=us-central1
gcloud run jobs executions logs karlcam-collector-v2 --region=us-central1
```

## Environment Variables

### Required for all Python services
- `DATABASE_URL`: PostgreSQL connection string (format: `postgresql://user:password@host:port/database`)
- `BUCKET_NAME`: Cloud Storage bucket name (default: `karlcam-fog-data`)

### Service-specific
- `USE_CLOUD_STORAGE`: Enable Cloud Storage integration (default: `true`)
- `PROJECT_ID`: Google Cloud project ID
- `REGION`: Deployment region (default: `us-central1`)

## Key Implementation Details

### Image Collection
- Images are fetched from webcams defined in the database
- Each collection run is tracked with success/failure metrics
- Images are stored in Cloud Storage at `gs://karlcam-fog-data/raw_images/`
- Filename format: `{webcam_id}_{timestamp}.jpg`

### Fog Labeling System
- Multiple labelers can process the same image (Gemini, Gemini Masked, etc.)
- Each labeler produces:
  - `fog_score`: 0-100 numerical score
  - `fog_level`: Categorical (Clear, Light Fog, Moderate Fog, Heavy Fog, Very Heavy Fog)
  - `confidence`: 0-1 confidence score
  - `reasoning`: Text explanation
  - Additional metadata in `label_data` JSON field

### API Endpoints
- `/api/public/cameras`: List all active webcams
- `/api/public/cameras/{id}/latest`: Get latest image and labels
- `/api/public/cameras/{id}/history`: Get historical data
- `/api/public/stats`: System statistics

## Testing

Currently no automated tests are configured. When implementing tests:
- Python: Use pytest for backend services
- React: Use Jest (via `npm test`) for frontend components
- Integration: Test against staging environment

## Database Connections

### Local Development Database Access

When working locally, use `make start-sql` to start a single Cloud SQL proxy on the default PostgreSQL port 5432. The proxy connects to the database instance, allowing access to all databases through the same port.

**Important**: Before running `make start-sql`, check if the proxy is already running:
```bash
# Check if Cloud SQL proxy is already running on port 5432
lsof -i :5432
```

If the proxy is already running, you can skip `make start-sql` and connect directly to the database.

#### Connecting with psql

```bash
# Get the database password (read from .env file for transparency)
# Read .env file first to see the password, then use it in commands

# Connect to staging database
psql "postgresql://karlcam_staging:${KARLCAM_DB_PASSWORD}@localhost:5432/karlcam_staging"

# Connect to production database (empty database)
psql "postgresql://karlcam_production:${KARLCAM_DB_PASSWORD}@localhost:5432/karlcam_production"

# Connect to v2 database (production data)
psql "postgresql://karlcam_v2:${KARLCAM_DB_PASSWORD}@localhost:5432/karlcam_v2"
```

### Database Details

All databases are hosted on Cloud SQL instance `karlcam:us-central1:karlcam-db` and accessible through a single local proxy on port 5432:

#### Staging Database: `karlcam_staging`
- Contains staging/development data
- 12 webcams configured

#### Production Database: `karlcam_production`  
- Currently empty (no tables)
- Reserved for future use

#### V2 Database: `karlcam_v2`
- Contains current production data
- 12 webcams configured

## Common Tasks

### Adding a New Webcam
1. Insert into `webcams` table with required fields (id, name, url, latitude, longitude)
2. Set `active=true` to include in collection runs
3. Webcam will be included in next collection cycle

### Debugging Collection Issues
1. Check Cloud Run Jobs logs: `gcloud run jobs executions logs karlcam-collector-v2`
2. Query `collection_runs` table for summary statistics
3. Check `image_collections` for successful captures
4. Verify Cloud Storage permissions and bucket access

### Monitoring Label Quality
1. Query `image_labels` table filtering by `labeler_name`
2. Compare confidence scores across different labelers
3. Review `reasoning` field for explanation quality
4. Check label distribution for anomalies

## Commit Message Format

All commits must start with either `fix:` or `feat:` followed by a concise description:

- `fix:` - Bug fixes, corrections, or improvements to existing functionality
- `feat:` - New features or significant additions

Examples from recent commits:
- `fix: api env var logic`
- `fix: use OUTPUT_BUCKET env var for collector job`
- `fix: collector sql`
- `feat: move db to shared`
- `fix: remove secrets`
- `fix: trim back cloud permissions`

Keep commit messages concise and descriptive. Focus on what was changed, not why.

**IMPORTANT**: Do not include any mention of "Claude Code", "Generated with Claude Code", or similar AI attribution in commit messages. Keep commits clean and professional.