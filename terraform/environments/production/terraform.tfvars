# KarlCam Production Environment Configuration

# Basic Configuration
project_id  = "karlcam"
region      = "us-central1"
environment = "production"

# Domains - Main production domains
domain              = "karl.cam"
api_subdomain       = "api"
admin_subdomain     = "admin"
admin_api_subdomain = "admin-api"

# Storage
bucket_name = "karlcam-production-data"

# Resource Limits (Higher for production load)
max_api_instances      = 10
max_frontend_instances = 5
max_admin_instances    = 3

# Production pipeline schedule  
pipeline_schedule = "*/10 * * * *"  # Every 10 minutes - unified pipeline


# Production-specific settings
auto_scaling_min_instances = 1
auto_scaling_max_instances = 10