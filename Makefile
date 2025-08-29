.PHONY: help start-api start-frontend start-review-backend start-review-frontend start-collect start-collect-ffmpeg start-sql clean

# Default target
help:
	@echo "Available targets:"
	@echo "  start-api            - Setup and start the API server (http://localhost:8002)"
	@echo "  start-frontend       - Setup and start the main frontend development server (http://localhost:3000)"
	@echo "  start-review-backend - Setup and start the review backend server (http://localhost:8001)"
	@echo "  start-review-frontend- Setup and start the review frontend development server (http://localhost:3001)"
	@echo "  start-collect        - Setup and run the dual scoring collector locally"
	@echo "  start-collect-ffmpeg - Run collector using ffmpeg for video streams"
	@echo "  start-sql           - Start Cloud SQL Proxy for local development"
	@echo "  clean               - Remove virtual environments and node_modules"

# API: setup venv + install deps + start
start-api:
	@echo "Setting up and starting API server..."
	cd api && python3 -m venv venv || true
	cd api && source venv/bin/activate && pip install -r requirements.txt
	@echo "Starting API server on http://localhost:8002"
	cd api && source venv/bin/activate && python main.py

# Frontend: npm install + start
start-frontend:
	@echo "Setting up and starting frontend development server..."
	cd frontend && npm install
	@echo "Starting frontend development server on http://localhost:3000"
	cd frontend && npm start

# Review backend: setup venv + install deps + start
start-review-backend:
	@echo "Setting up and starting review backend server..."
	cd review/backend && python3 -m venv venv
	cd review/backend && source venv/bin/activate && pip install -r requirements.txt
	@echo "Starting review backend server on http://localhost:8001"
	cd review/backend && source venv/bin/activate && python main.py

# Review frontend: npm install + start
start-review-frontend:
	@echo "Setting up and starting review frontend development server..."
	cd review/frontend && npm install
	@echo "Starting review frontend development server on http://localhost:3001"
	cd review/frontend && npm start

# Collector: setup venv + install deps + run
start-collect:
	@echo "Setting up and running dual scoring collector..."
	rm -rf collect/venv
	cd collect && python3.12 -m venv venv
	cd collect && source venv/bin/activate && pip install -r requirements.txt
	@echo "📁 Creating test directories..."
	@mkdir -p test_data/{raw/{images,labels},review/{pending,metadata}}
	@echo "🚀 Running collector..."
	@echo "📊 Data will be saved to ./test_data/"
	PYTHONPATH=/Users/reed/Code/Homelab/KarlCam collect/venv/bin/python -m collect.collect_and_label

# Collector with ffmpeg: check ffmpeg + setup venv + run
start-collect-ffmpeg:
	@echo "Setting up and running collector with ffmpeg support..."
	@which ffmpeg > /dev/null || (echo "❌ ffmpeg not found! Install with: brew install ffmpeg" && exit 1)
	@echo "✅ ffmpeg found"
	rm -rf collect/venv
	cd collect && python3 -m venv venv
	cd collect && source venv/bin/activate && pip install -r requirements.txt
	@echo "📁 Creating test directories..."
	@mkdir -p test_data/{raw/{images,labels},review/{pending,metadata}}
	@echo "🚀 Running collector with ffmpeg..."
	@echo "📊 Data will be saved to ./test_data/"
	cd collect && source venv/bin/activate && python -m collect_with_ffmpeg

# Cloud SQL Proxy: start proxy for local development
start-sql:
	@echo "🔌 Starting Cloud SQL Proxy for local development..."
	@echo "📍 Connecting to: karlcam:us-central1:karlcam-db"
	@echo "🔗 Local port: 5432"
	@echo ""
	@echo "To use in another terminal, set these environment variables:"
	@echo "  export DATABASE_URL=\"postgresql://karlcam:<password>@localhost:5432/karlcam\""
	@echo "  export BUCKET_NAME=\"karlcam-fog-data\""
	@echo ""
	@echo "Get the password with:"
	@echo "  gcloud secrets versions access latest --secret=\"karlcam-db-password\" --project=karlcam"
	@echo ""
	@echo "Press Ctrl+C to stop the proxy"
	@echo "----------------------------------------"
	cloud-sql-proxy karlcam:us-central1:karlcam-db --port 5432 --gcloud-auth

# Clean up
clean:
	@echo "Cleaning up virtual environments and node_modules..."
	rm -rf api/venv
	rm -rf review/backend/venv
	rm -rf collect/venv
	rm -rf frontend/node_modules
	rm -rf review/frontend/node_modules
	@echo "Cleanup complete!"