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

# More frequent collection for testing
collector_schedule = "0 */2 * * *"  # Every 2 hours
labeler_schedule   = "15 1 * * *"   # Daily at 1:15 AM


# Staging-specific settings
auto_scaling_min_instances = 0
auto_scaling_max_instances = 3