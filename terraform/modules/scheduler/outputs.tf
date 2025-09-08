# Scheduler Module Outputs

output "collector_job_schedule_name" {
  description = "Name of the collector scheduler job"
  value       = google_cloud_scheduler_job.collector.name
}

output "labeler_job_schedule_name" {
  description = "Name of the labeler scheduler job"
  value       = google_cloud_scheduler_job.labeler.name
}

output "collector_schedule" {
  description = "Collector job cron schedule"
  value       = google_cloud_scheduler_job.collector.schedule
}

output "labeler_schedule" {
  description = "Labeler job cron schedule"
  value       = google_cloud_scheduler_job.labeler.schedule
}