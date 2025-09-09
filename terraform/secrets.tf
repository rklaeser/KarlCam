# KarlCam Secret Manager Resources

# Secret for Database Connection URL
resource "google_secret_manager_secret" "database_url" {
  secret_id = "database-url-${var.environment}"
  project   = var.project_id

  replication {
    auto {
    }
  }

  labels = {
    environment = var.environment
    component   = "database"
  }
}

# Database URL Secret Version
resource "google_secret_manager_secret_version" "database_url" {
  secret      = google_secret_manager_secret.database_url.id
  secret_data = "postgresql://karlcam_${var.environment}:${var.database_password}@/karlcam_${var.environment}?host=/cloudsql/${data.terraform_remote_state.shared.outputs.sql_instance_connection_name}"

  depends_on = [
    data.terraform_remote_state.shared
  ]
}

# Secret for Gemini API Key
resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "gemini-api-key-${var.environment}"
  project   = var.project_id

  replication {
    auto {
    }
  }

  labels = {
    environment = var.environment
    component   = "ai"
  }
}

# Gemini API Key Secret Version
resource "google_secret_manager_secret_version" "gemini_api_key" {
  secret      = google_secret_manager_secret.gemini_api_key.id
  secret_data = var.gemini_api_key
}

# Optional: Secret for Database Password (separate from connection string)
resource "google_secret_manager_secret" "database_password" {
  secret_id = "karlcam-db-password-${var.environment}"
  project   = var.project_id

  replication {
    auto {
    }
  }

  labels = {
    environment = var.environment
    component   = "database"
  }
}

# Database Password Secret Version
resource "google_secret_manager_secret_version" "database_password" {
  secret      = google_secret_manager_secret.database_password.id
  secret_data = var.database_password
}

# IAM binding for secrets access
resource "google_secret_manager_secret_iam_binding" "database_url_access" {
  secret_id = google_secret_manager_secret.database_url.secret_id
  role      = "roles/secretmanager.secretAccessor"
  members = [
    "serviceAccount:${local.service_account_email}",
  ]
}

resource "google_secret_manager_secret_iam_binding" "gemini_api_key_access" {
  secret_id = google_secret_manager_secret.gemini_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  members = [
    "serviceAccount:${local.service_account_email}",
  ]
}

resource "google_secret_manager_secret_iam_binding" "database_password_access" {
  secret_id = google_secret_manager_secret.database_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  members = [
    "serviceAccount:${local.service_account_email}",
  ]
}