# KarlCam Cloud Scheduler Configuration
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
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.karlcam_collector.name}:run"

    oauth_token {
      service_account_email = local.service_account_email
    }
  }

  depends_on = [
    data.terraform_remote_state.shared,
    google_cloud_run_v2_job.karlcam_collector
  ]
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
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.karlcam_labeler.name}:run"

    oauth_token {
      service_account_email = local.service_account_email
    }
  }

  depends_on = [
    data.terraform_remote_state.shared,
    google_cloud_run_v2_job.karlcam_labeler
  ]
}

# Additional IAM permission for Cloud Scheduler
resource "google_project_iam_member" "scheduler_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${local.service_account_email}"
}

# Optional: Monitoring for failed scheduled jobs
resource "google_monitoring_alert_policy" "scheduler_failures" {
  count        = var.environment == "prod" ? 1 : 0
  display_name = "KarlCam Scheduler Job Failures"
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

  depends_on = [data.terraform_remote_state.shared]
}