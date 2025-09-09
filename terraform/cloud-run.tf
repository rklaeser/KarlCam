# KarlCam Cloud Run Services and Jobs

# Cloud Run API Service
resource "google_cloud_run_v2_service" "karlcam_api" {
  name     = "karlcam-api-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    service_account = local.service_account_email
    
    annotations = {
      "run.googleapis.com/cloudsql-instances" = data.terraform_remote_state.shared.outputs.sql_instance_connection_name
    }
    
    containers {
      image = "gcr.io/${var.project_id}/karlcam-api:${var.image_tag}"
      
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      
      env {
        name  = "BUCKET_NAME"
        value = var.bucket_name
      }
      
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database_url.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      ports {
        container_port = 8002
      }
    }

    scaling {
      min_instance_count = var.auto_scaling_min_instances
      max_instance_count = var.max_api_instances
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  depends_on = [
    data.terraform_remote_state.shared
  ]
}

# Cloud Run Frontend Service
resource "google_cloud_run_v2_service" "karlcam_frontend" {
  name     = "karlcam-frontend-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    service_account = local.service_account_email
    
    containers {
      image = "gcr.io/${var.project_id}/karlcam-frontend:${var.image_tag}"

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      ports {
        container_port = 80
      }
    }

    scaling {
      min_instance_count = var.auto_scaling_min_instances
      max_instance_count = var.max_frontend_instances
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  depends_on = [data.terraform_remote_state.shared]
}

# Cloud Run Admin Backend Service
resource "google_cloud_run_v2_service" "karlcam_admin_backend" {
  name     = "karlcam-admin-backend-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    service_account = local.service_account_email
    
    annotations = {
      "run.googleapis.com/cloudsql-instances" = data.terraform_remote_state.shared.outputs.sql_instance_connection_name
    }
    
    containers {
      image = "gcr.io/${var.project_id}/karlcam-admin-backend:${var.image_tag}"
      
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      
      env {
        name  = "BUCKET_NAME"
        value = var.bucket_name
      }
      
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database_url.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      ports {
        container_port = 8001
      }
    }

    scaling {
      min_instance_count = var.auto_scaling_min_instances
      max_instance_count = var.max_admin_instances
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  depends_on = [
    data.terraform_remote_state.shared
  ]
}

# Cloud Run Admin Frontend Service
resource "google_cloud_run_v2_service" "karlcam_admin_frontend" {
  name     = "karlcam-admin-frontend-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    service_account = local.service_account_email
    
    containers {
      image = "gcr.io/${var.project_id}/karlcam-admin-frontend:${var.image_tag}"

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      ports {
        container_port = 80
      }
    }

    scaling {
      min_instance_count = var.auto_scaling_min_instances
      max_instance_count = var.max_admin_instances
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  depends_on = [data.terraform_remote_state.shared]
}

# Cloud Run Job - Data Collector
resource "google_cloud_run_v2_job" "karlcam_collector" {
  name     = "karlcam-collector-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    template {
      service_account = local.service_account_email
      
      containers {
        image = "gcr.io/${var.project_id}/karlcam-collector:${var.image_tag}"
        
        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }
        
        env {
          name  = "BUCKET_NAME"
          value = var.bucket_name
        }
        
        env {
          name = "DATABASE_URL"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.database_url.secret_id
              version = "latest"
            }
          }
        }

        resources {
          limits = {
            cpu    = "2"
            memory = "2Gi"
          }
        }
      }

      max_retries = 1
    }
  }

  depends_on = [
    data.terraform_remote_state.shared
  ]
}

# Cloud Run Job - Image Labeler
resource "google_cloud_run_v2_job" "karlcam_labeler" {
  name     = "karlcam-labeler-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    template {
      service_account = local.service_account_email
      
      containers {
        image = "gcr.io/${var.project_id}/karlcam-labeler:${var.image_tag}"
        
        env {
          name  = "USE_CLOUD_STORAGE"
          value = "true"
        }
        
        env {
          name  = "OUTPUT_BUCKET"
          value = var.bucket_name
        }
        
        env {
          name = "DATABASE_URL"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.database_url.secret_id
              version = "latest"
            }
          }
        }
        
        env {
          name = "GEMINI_API_KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.gemini_api_key.secret_id
              version = "latest"
            }
          }
        }

        resources {
          limits = {
            cpu    = "1"
            memory = "2Gi"
          }
        }
      }

      max_retries = 1
    }
  }

  depends_on = [
    data.terraform_remote_state.shared
  ]
}

# IAM Policy - Allow unauthenticated access to public services
resource "google_cloud_run_service_iam_binding" "api_public" {
  location = google_cloud_run_v2_service.karlcam_api.location
  service  = google_cloud_run_v2_service.karlcam_api.name
  role     = "roles/run.invoker"
  members  = ["allUsers"]
}

resource "google_cloud_run_service_iam_binding" "frontend_public" {
  location = google_cloud_run_v2_service.karlcam_frontend.location
  service  = google_cloud_run_v2_service.karlcam_frontend.name
  role     = "roles/run.invoker"
  members  = ["allUsers"]
}

# Admin services remain private (no public IAM binding)