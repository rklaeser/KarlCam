# KarlCam Shared Infrastructure Configuration

# Basic Configuration
project_id = "karlcam"
region     = "us-central1"

# SQL Instance Configuration (shared across environments)
sql_instance_tier           = "db-f1-micro"
enable_deletion_protection  = true
backup_retention_days       = 7