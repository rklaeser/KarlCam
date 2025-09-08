# KarlCam Shared Infrastructure
# Resources shared across all environments

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Cloud SQL Instance - Shared across environments
resource "google_sql_database_instance" "karlcam_db" {
  name             = "karlcam-db"
  database_version = "POSTGRES_15"
  region          = var.region
  project         = var.project_id

  settings {
    tier                        = var.sql_instance_tier
    availability_type          = "ZONAL"
    disk_type                  = "PD_SSD"
    disk_size                  = 10
    disk_autoresize            = true
    disk_autoresize_limit      = 100
    deletion_protection_enabled = var.enable_deletion_protection

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = var.backup_retention_days
      backup_retention_settings {
        retained_backups = var.backup_retention_days
      }
    }

    maintenance_window {
      day          = 7
      hour         = 4
      update_track = "stable"
    }

    database_flags {
      name  = "cloudsql.iam_authentication"
      value = "on"
    }

    ip_configuration {
      ipv4_enabled    = true
      authorized_networks {
        name  = "allow-all"
        value = "0.0.0.0/0"
      }
    }
  }

  deletion_protection = var.enable_deletion_protection

  lifecycle {
    prevent_destroy = true
  }
}

# Service Account for KarlCam Backend - Shared
resource "google_service_account" "karlcam_backend" {
  account_id   = "karlcam-backend"
  display_name = "KarlCam Backend Service Account"
  description  = "Service account for KarlCam backend services"
  project      = var.project_id
}

# IAM Bindings for Backend Service Account
resource "google_project_iam_member" "karlcam_backend_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.karlcam_backend.email}"
}

resource "google_project_iam_member" "karlcam_backend_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.karlcam_backend.email}"
}

resource "google_project_iam_member" "karlcam_backend_secrets" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.karlcam_backend.email}"
}

resource "google_project_iam_member" "karlcam_backend_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.karlcam_backend.email}"
}

resource "google_project_iam_member" "karlcam_backend_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.karlcam_backend.email}"
}

resource "google_project_iam_member" "karlcam_backend_artifact_registry" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.karlcam_backend.email}"
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "sqladmin.googleapis.com",
    "run.googleapis.com",
    "cloudscheduler.googleapis.com",
    "secretmanager.googleapis.com",
    "compute.googleapis.com",
    "cloudbuild.googleapis.com",
    "containerregistry.googleapis.com",
    "artifactregistry.googleapis.com"
  ])

  project = var.project_id
  service = each.key

  disable_on_destroy = false
}