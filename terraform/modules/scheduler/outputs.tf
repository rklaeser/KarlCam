# Scheduler Module Outputs

output "pipeline_job_schedule_name" {
  description = "Name of the unified pipeline scheduler job"
  value       = google_cloud_scheduler_job.pipeline.name
}

output "pipeline_schedule" {
  description = "Pipeline job cron schedule"
  value       = google_cloud_scheduler_job.pipeline.schedule
}