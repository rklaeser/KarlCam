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

# Production collection schedule
collector_schedule = "*/15 7-18 * * *"  # Every 15 minutes, 7am-6:45pm
labeler_schedule   = "7,22,37,52 7-18 * * *"  # Every 15 minutes offset by 7 min, 7:07am-6:52pm


# Production-specific settings
auto_scaling_min_instances = 1
auto_scaling_max_instances = 10