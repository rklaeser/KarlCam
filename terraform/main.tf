# KarlCam Environment-Specific Infrastructure
# Storage and environment-specific database resources

# Data source to reference shared SQL instance
data "terraform_remote_state" "shared" {
  backend = "local"
  config = {
    path = "${path.module}/shared/terraform.tfstate"
  }
}

# Environment-specific Database
resource "google_sql_database" "karlcam_db" {
  name     = "karlcam_${var.environment}"
  instance = data.terraform_remote_state.shared.outputs.sql_instance_name
  project  = var.project_id
}

# Environment-specific Database User
resource "google_sql_user" "karlcam_db_user" {
  name     = "karlcam_${var.environment}"
  instance = data.terraform_remote_state.shared.outputs.sql_instance_name
  password = var.database_password
  project  = var.project_id
}

# Cloud Storage Buckets
resource "google_storage_bucket" "karlcam_data" {
  name          = var.bucket_name
  location      = var.region
  project       = var.project_id
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }
}

# Reference to shared resources
locals {
  service_account_email = data.terraform_remote_state.shared.outputs.service_account_email
}

