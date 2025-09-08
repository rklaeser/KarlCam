# KarlCam

A serverless webcam monitoring and analysis system built on Google Cloud Platform. KarlCam  collects images from webcams across San Francisco, analyzes them, and provides a public interface to view current conditions and historical data.

## 🏗️ Architecture

KarlCam uses a modern serverless architecture on Google Cloud:

- **Data Collection**: Cloud Run Job that periodically collects webcam images
- **API Backend**: Cloud Run service providing REST endpoints
- **Public Frontend**: React application for viewing webcam data
- **Admin System**: Management interface for system administration
- **Storage**: Cloud SQL (PostgreSQL) for metadata, Cloud Storage for images
- **CI/CD**: Cloud Build with GitHub integration

## 🚀 Quick Start

### Prerequisites

- Google Cloud Project with billing enabled
- GitHub repository connected to Cloud Build
- `gcloud` CLI installed and authenticated

### Deployment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/reedkle/KarlCam.git
   cd KarlCam
   ```

2. **Deploy infrastructure:**
   ```bash
   ./infra/deploy-v2.sh infrastructure
   ```

3. **Deploy all services:**
   ```bash
   ./infra/deploy-v2.sh all
   ```

4. **Or deploy individual components:**
   ```bash
   ./infra/deploy-v2.sh collector    # Data collection job
   ./infra/deploy-v2.sh api         # API service  
   ./infra/deploy-v2.sh frontend    # Public frontend
   ./infra/deploy-v2.sh admin       # Admin system
   ```

## 🏃‍♂️ Running Locally

### Backend Development

1. **Set up Python environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or: venv\Scripts\activate  # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r web/api/requirements.txt
   pip install -r collect/requirements.txt
   ```

3. **Set up database:**
   ```bash
   python -m db.init_db
   ```

4. **Run API server:**
   ```bash
   cd web/api
   python main.py
   ```

### Frontend Development

1. **Install dependencies:**
   ```bash
   cd web/frontend
   npm install
   ```

2. **Start development server:**
   ```bash
   npm start
   ```

3. **Build for production:**
   ```bash
   npm run build
   ```

### Admin Interface

1. **Install dependencies:**
   ```bash
   cd admin/frontend
   npm install
   ```

2. **Start admin interface:**
   ```bash
   npm start
   ```

## 🔧 Configuration

### Environment Variables

- `PROJECT_ID`: Google Cloud project ID
- `REGION`: Deployment region (default: us-central1)
- `BUCKET_NAME`: Cloud Storage bucket name
- `DATABASE_URL`: PostgreSQL connection string

### Webcam Sources

Webcam URLs are configured in `data/webcams.json`. Add new sources by updating this file with:

```json
{
  "name": "webcam-name",
  "url": "https://example.com/webcam.jpg",
  "location": {
    "lat": 37.7749,
    "lng": -122.4194
  },
  "description": "Webcam description"
}
```

## 📊 API Endpoints

### Public API

- `GET /api/public/cameras` - List all webcams
- `GET /api/public/cameras/{id}` - Get specific webcam data
- `GET /api/public/cameras/{id}/latest` - Get latest image
- `GET /api/public/cameras/{id}/history` - Get historical data

### Admin API

- `GET /api/admin/stats` - System statistics
- `POST /api/admin/collect` - Trigger manual collection
- `GET /api/admin/logs` - View system logs

## 🏗️ Project Structure

```
KarlCam/
├── collect/           # Data collection service
├── web/
│   ├── api/          # REST API backend
│   └── frontend/     # Public React frontend
├── admin/
│   ├── backend/      # Admin API
│   └── frontend/     # Admin React interface
├── db/               # Database models and utilities
├── infra/            # Deployment scripts and Dockerfiles
├── data/             # Configuration and sample data
└── cloudbuild.yaml   # CI/CD configuration
```

## 🚀 CI/CD Pipeline

KarlCam uses Cloud Build for automated deployments:

1. **Trigger**: Push to `main` branch
2. **Build**: All Docker images built in parallel
3. **Test**: Run npm ci for frontend builds
4. **Deploy**: Deploy to Cloud Run services
5. **Monitor**: Logs available in Cloud Console

### Manual Build

```bash
gcloud builds submit --config=cloudbuild.yaml
```

## 🔐 Security

- **Authentication**: Service accounts for inter-service communication
- **Authorization**: IAM roles and permissions
- **Network**: VPC and firewall rules
- **Data**: Encrypted at rest and in transit

## 🐛 Troubleshooting

### Common Issues

1. **Build failures**: Check Cloud Build logs in Console
2. **Permission errors**: Verify IAM roles for service accounts
3. **Database connection**: Ensure Cloud SQL is accessible
4. **Missing images**: Check Cloud Storage permissions

### Useful Commands

```bash
# View recent builds
gcloud builds list --limit=5

# Check service logs
gcloud run logs read karlcam-api-v2 --region=us-central1

# Run collector manually
gcloud run jobs execute karlcam-collector-v2 --region=us-central1

# Check service status
gcloud run services list --region=us-central1
```

## 📈 Monitoring

- **Cloud Run**: Built-in metrics and logging
- **Cloud SQL**: Performance insights
- **Cloud Storage**: Usage metrics
- **Custom**: Application-level monitoring via API

## 💰 Cost Optimization

KarlCam is designed for cost efficiency:

- **Serverless**: Pay only for actual usage
- **Estimated cost**: ~$5-15/month for typical usage
- **Optimization**: Automatic scaling to zero when idle

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and test locally
4. Submit a pull request
5. Automated builds will test your changes

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♂️ Support

- **Issues**: GitHub Issues
- **Documentation**: This README and inline code comments
- **Logs**: Cloud Console for deployment and runtime issues

---

Built with ❤️ for San Francisco webcam enthusiasts