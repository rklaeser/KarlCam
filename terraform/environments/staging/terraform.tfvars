# KarlCam Staging Environment Configuration

# Basic Configuration
project_id  = "karlcam"  # Use same project with staging naming
region      = "us-central1"
environment = "staging"

# Domains - Use staging subdomains
domain              = "staging.karl.cam"
api_subdomain       = "api"
admin_subdomain     = "admin"
admin_api_subdomain = "admin-api"

# Storage
bucket_name = "karlcam-staging-data"

# Resource Limits (Lower for cost optimization)
max_api_instances      = 3
max_frontend_instances = 2
max_admin_instances    = 2

# Pipeline schedule for testing
pipeline_schedule = "*/30 * * * *"  # Every 30 minutes for staging


# Staging-specific settings
auto_scaling_min_instances = 0
auto_scaling_max_instances = 3