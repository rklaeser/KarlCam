# KarlCam

A serverless webcam monitoring and fog detection system built on Google Cloud Platform. KarlCam collects images from webcams across San Francisco, analyzes them for fog conditions using AI, and provides public and admin interfaces to view the data.

## 🏗️ Architecture

KarlCam uses a modern serverless architecture on Google Cloud:

- **Unified Pipeline**: Single Cloud Run Job that collects images and analyzes them for fog conditions
- **API Backend**: FastAPI service providing REST endpoints for public data access
- **Public Frontend**: React application for viewing webcam data and fog conditions
- **Admin System**: Management interface for system administration
- **Storage**: Cloud SQL (PostgreSQL) for metadata, Cloud Storage for images
- **Infrastructure**: Terraform-managed GCP resources
- **CI/CD**: Cloud Build with automated deployments

## 🚀 Quick Start

### Prerequisites

- Google Cloud Project with billing enabled
- GitHub repository connected to Cloud Build
- `gcloud` CLI installed and authenticated
- Terraform installed (v1.5+)

### Deployment

KarlCam uses Cloud Build for automated deployments. Push to the `main` branch triggers production deployment, while `staging` branch triggers staging deployment.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Klaeser-Homelab/KarlCam.git
   cd KarlCam
   ```

2. **Manual deployment via Cloud Build:**
   ```bash
   gcloud builds submit --config=cloudbuild.yaml
   ```

3. **Deploy with Terraform (from terraform/ directory):**
   ```bash
   terraform init -backend-config="bucket=karlcam-terraform-state" \
                  -backend-config="prefix=terraform/state/production"
   terraform plan -var-file="environments/production/terraform.tfvars"
   terraform apply -var-file="environments/production/terraform.tfvars"
   ```

## 🏃‍♂️ Running Locally

### Local Development Setup

1. **Start Cloud SQL Proxy (required for local development):**
   ```bash
   make start-sql
   ```

2. **Get database password:**
   ```bash
   gcloud secrets versions access latest --secret="karlcam-db-password" --project=karlcam
   ```

3. **Start individual services:**
   ```bash
   make start-api            # API server on http://localhost:8002
   make start-frontend       # Frontend on http://localhost:3000
   make start-admin-backend  # Admin API on http://localhost:8001
   make start-admin-frontend # Admin UI on http://localhost:3001
   make start-pipeline       # Run unified pipeline locally
   ```

### Python Development

1. **Set up Python environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies for specific service:**
   ```bash
   pip install -r web/api/requirements.txt
   pip install -r pipeline/requirements.txt
   ```

3. **Initialize database:**
   ```bash
   python -m db.init_db
   ```

### Frontend Development

1. **Web frontend:**
   ```bash
   cd web/frontend
   npm install
   npm start         # Development server on http://localhost:3000
   npm run build     # Production build
   npm test          # Run tests
   ```

2. **Admin frontend:**
   ```bash
   cd admin/frontend
   npm install
   npm start         # Development server on http://localhost:3001
   npm run build     # Production build
   ```

## 🔧 Configuration

### Environment Variables

#### Required for all Python services
- `DATABASE_URL`: PostgreSQL connection string (format: `postgresql://user:password@host:port/database`)
- `BUCKET_NAME`: Cloud Storage bucket name (default: `karlcam-fog-data`)

#### Service-specific
- `USE_CLOUD_STORAGE`: Enable Cloud Storage integration (default: `true`)
- `PROJECT_ID`: Google Cloud project ID
- `REGION`: Deployment region (default: `us-central1`)

## 📊 API Endpoints

### Public API

- `GET /api/public/cameras` - List all active webcams
- `GET /api/public/cameras/{id}/latest` - Get latest image and labels
- `GET /api/public/cameras/{id}/history` - Get historical data
- `GET /api/public/stats` - System statistics
- `GET /api/system/status` - System status and mode


## 🏗️ Project Structure

```
KarlCam/
├── pipeline/         # Unified data collection and labeling service (Cloud Run Job)
│   ├── labelers/     # Different labeler implementations (Gemini, Gemini Masked)
│   ├── collect_and_label.py # Main pipeline script
│   ├── requirements.txt
│   └── Dockerfile.prod
├── web/
│   ├── api/          # FastAPI backend service
│   │   └── infra/    # API Dockerfile and configs
│   └── frontend/     # Public React frontend
│       └── infra/    # Frontend Dockerfile and configs
├── admin/
│   ├── backend/      # Admin API service
│   │   └── infra/    # Admin backend Dockerfile
│   └── frontend/     # Admin React interface
│       └── infra/    # Admin frontend Dockerfile
├── db/               # Database models and schema
│   └── infra/        # Database initialization scripts
├── terraform/        # Infrastructure as Code
│   ├── environments/ # Environment-specific configs
│   ├── modules/      # Reusable Terraform modules
│   └── scripts/      # Deployment helper scripts
├── data/             # Configuration data
├── training/         # ML training resources
├── Makefile          # Local development commands
└── cloudbuild.yaml   # CI/CD pipeline configuration
```

## 🚀 CI/CD Pipeline

KarlCam uses Cloud Build for automated deployments:

1. **Triggers**: 
   - `main` branch → Production deployment
   - `staging` branch → Staging deployment
2. **Build**: All Docker images built in parallel
3. **Push**: Images pushed to Google Container Registry
4. **Infrastructure**: Terraform applies environment-specific configs
5. **Deploy**: Services deployed to Cloud Run
6. **Schedule**: Cloud Scheduler jobs configured for data collection

## 💰 Cost Optimization

KarlCam is designed for cost efficiency:

- **Serverless Architecture**: Pay only for actual usage
- **Scheduled Collection**: Runs only during specified hours (7am-7pm)
- **Auto-scaling**: Services scale to zero when idle
- **Efficient Storage**: Images stored in Cloud Storage with lifecycle policies
- **Estimated Cost**: ~$10-30/month for production usage

## 📊 Database Schema

Key tables:
- `webcams`: Camera configurations and metadata
- `collection_runs`: Tracking of collection job executions
- `image_collections`: Raw collected images metadata
- `image_labels`: AI-generated labels for fog analysis
- `system_status`: System state tracking

## 🔍 Fog Detection

The system uses Gemini AI to analyze images for fog conditions:
- **Fog Score**: 0-100 numerical score
- **Fog Level**: Clear, Light Fog, Moderate Fog, Heavy Fog, Very Heavy Fog
- **Confidence**: 0-1 confidence score
- **Multiple Labelers**: Support for different labeling strategies

## 📝 License

This project is open source and available under the MIT License.
