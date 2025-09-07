# KarlCam Staging Environment Configuration

# Basic Configuration
project_id  = "karlcam-staging"  # Or use same project with different naming
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

# Shorter backup retention for staging
backup_retention_days = 3

# Disable deletion protection for easier testing
enable_deletion_protection = false

# Staging-specific settings
sql_instance_tier = "db-f1-micro"
auto_scaling_min_instances = 0
auto_scaling_max_instances = 3