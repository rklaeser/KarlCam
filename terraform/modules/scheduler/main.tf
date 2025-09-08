# KarlCam Scheduler Module
# Automated job scheduling for data collection and processing

# Cloud Scheduler Job - Data Collector
resource "google_cloud_scheduler_job" "collector" {
  name        = "karlcam-collector-schedule-${var.environment}"
  description = "Automated KarlCam data collection job"
  schedule    = var.collector_schedule
  time_zone   = "America/Los_Angeles"
  region      = var.region
  project     = var.project_id

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${var.collector_job_name}:run"

    oauth_token {
      service_account_email = var.service_account_email
    }
  }
}

# Cloud Scheduler Job - Image Labeler
resource "google_cloud_scheduler_job" "labeler" {
  name        = "karlcam-labeler-schedule-${var.environment}"
  description = "Automated KarlCam image labeling job"
  schedule    = var.labeler_schedule
  time_zone   = "America/Los_Angeles"
  region      = var.region
  project     = var.project_id

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${var.labeler_job_name}:run"

    oauth_token {
      service_account_email = var.service_account_email
    }
  }
}

# Additional IAM permission for Cloud Scheduler
resource "google_project_iam_member" "scheduler_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${var.service_account_email}"
}

# Optional: Monitoring for failed scheduled jobs
resource "google_monitoring_alert_policy" "scheduler_failures" {
  display_name = "KarlCam Scheduler Job Failures - ${var.environment}"
  combiner     = "OR"
  project      = var.project_id

  conditions {
    display_name = "Collector job failures"
    condition_threshold {
      filter         = "resource.type=\"cloud_scheduler_job\" AND resource.labels.job_id=\"${google_cloud_scheduler_job.collector.name}\""
      comparison     = "COMPARISON_GT"
      threshold_value = 0
      duration       = "300s"

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  conditions {
    display_name = "Labeler job failures"
    condition_threshold {
      filter         = "resource.type=\"cloud_scheduler_job\" AND resource.labels.job_id=\"${google_cloud_scheduler_job.labeler.name}\""
      comparison     = "COMPARISON_GT"
      threshold_value = 0
      duration       = "300s"

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = []
}