# KarlCam Core Infrastructure
# Cloud SQL, Storage, and IAM configuration

# Cloud SQL Instance
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

# V2 Database
resource "google_sql_database" "karlcam_v2" {
  name     = "karlcam_${var.environment}"
  instance = google_sql_database_instance.karlcam_db.name
  project  = var.project_id
}

# V2 Database User
resource "google_sql_user" "karlcam_v2_user" {
  name     = "karlcam_${var.environment}"
  instance = google_sql_database_instance.karlcam_db.name
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

# Service Account for KarlCam Backend
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