# KarlCam Scheduler Module
# Automated job scheduling for data collection and processing


# Cloud Scheduler Job - Unified Pipeline (collect + label)
resource "google_cloud_scheduler_job" "pipeline" {
  name        = "karlcam-pipeline-schedule-${var.environment}"
  description = "Automated KarlCam unified pipeline job (collect and label)"
  schedule    = var.pipeline_schedule
  time_zone   = "America/Los_Angeles"
  region      = var.region
  project     = var.project_id

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${var.pipeline_job_name}:run"

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

# Optional: Monitoring for failed scheduled jobs (removed for now)
# TODO: Fix alert policy metric filters and re-enable monitoring