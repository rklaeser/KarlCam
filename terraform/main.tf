# KarlCam Environment-Specific Infrastructure
# Storage and environment-specific database resources

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
  
  backend "gcs" {
    # Configuration will be provided via init command
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Data source to reference shared SQL instance
data "terraform_remote_state" "shared" {
  backend = "gcs"
  config = {
    bucket = "karlcam-terraform-state"
    prefix = "terraform/state/shared"
  }
}

# Database resources are now managed in shared terraform

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

# Scheduler Module (Production Only)
module "scheduler" {
  count  = var.environment == "production" ? 1 : 0
  source = "./modules/scheduler"
  
  environment             = var.environment
  project_id              = var.project_id
  region                  = var.region
  collector_schedule      = var.collector_schedule
  labeler_schedule        = var.labeler_schedule
  pipeline_schedule       = var.pipeline_schedule
  collector_job_name      = google_cloud_run_v2_job.karlcam_collector.name
  labeler_job_name        = google_cloud_run_v2_job.karlcam_labeler.name
  pipeline_job_name       = google_cloud_run_v2_job.karlcam_pipeline.name
  service_account_email   = local.service_account_email
}

