# KarlCam Terraform Outputs

# Database Connection Info
output "database_instance_name" {
  description = "Cloud SQL instance name"
  value       = google_sql_database_instance.karlcam_db.name
}

output "database_connection_name" {
  description = "Cloud SQL connection name for Cloud Run services"
  value       = google_sql_database_instance.karlcam_db.connection_name
}

output "database_ip_address" {
  description = "Public IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.karlcam_db.public_ip_address
}

# Storage
output "bucket_name" {
  description = "Cloud Storage bucket name"
  value       = google_storage_bucket.karlcam_data.name
}

output "bucket_url" {
  description = "Cloud Storage bucket URL"
  value       = google_storage_bucket.karlcam_data.url
}

# Service Account
output "backend_service_account_email" {
  description = "Email of the backend service account"
  value       = google_service_account.karlcam_backend.email
}

# Cloud Run Services URLs
output "api_service_url" {
  description = "URL of the API Cloud Run service"
  value       = google_cloud_run_v2_service.karlcam_api.uri
}

output "frontend_service_url" {
  description = "URL of the frontend Cloud Run service"
  value       = google_cloud_run_v2_service.karlcam_frontend.uri
}

output "admin_backend_service_url" {
  description = "URL of the admin backend Cloud Run service"
  value       = google_cloud_run_v2_service.karlcam_admin_backend.uri
}

output "admin_frontend_service_url" {
  description = "URL of the admin frontend Cloud Run service"
  value       = google_cloud_run_v2_service.karlcam_admin_frontend.uri
}

# Cloud Run Jobs
output "collector_job_name" {
  description = "Name of the collector Cloud Run job"
  value       = google_cloud_run_v2_job.karlcam_collector.name
}

output "labeler_job_name" {
  description = "Name of the labeler Cloud Run job"
  value       = google_cloud_run_v2_job.karlcam_labeler.name
}

# Domain Mappings (when configured)
output "api_domain" {
  description = "API service domain"
  value       = "${var.api_subdomain}.${var.domain}"
}

output "frontend_domain" {
  description = "Frontend service domain"
  value       = var.domain
}

output "admin_domain" {
  description = "Admin interface domain"
  value       = "${var.admin_subdomain}.${var.domain}"
}

output "admin_api_domain" {
  description = "Admin API service domain"
  value       = "${var.admin_api_subdomain}.${var.domain}"
}

# Secrets
output "database_url_secret_name" {
  description = "Name of the database URL secret in Secret Manager"
  value       = google_secret_manager_secret.database_url.name
}

output "gemini_api_key_secret_name" {
  description = "Name of the Gemini API key secret in Secret Manager"
  value       = google_secret_manager_secret.gemini_api_key.name
}

# Project Info
output "project_id" {
  description = "Google Cloud project ID"
  value       = var.project_id
}

output "region" {
  description = "Google Cloud region"
  value       = var.region
}

# Quick Commands for Manual Operations
output "collector_run_command" {
  description = "Command to manually run the collector job"
  value       = "gcloud run jobs execute ${google_cloud_run_v2_job.karlcam_collector.name} --region=${var.region} --project=${var.project_id}"
}

output "labeler_run_command" {
  description = "Command to manually run the labeler job"
  value       = "gcloud run jobs execute ${google_cloud_run_v2_job.karlcam_labeler.name} --region=${var.region} --project=${var.project_id}"
}

output "api_logs_command" {
  description = "Command to view API service logs"
  value       = "gcloud run logs read ${google_cloud_run_v2_service.karlcam_api.name} --region=${var.region} --project=${var.project_id}"
}

# Database Connection String (for local development)
output "local_database_url" {
  description = "Database URL for local development (requires Cloud SQL proxy)"
  value       = "postgresql://${google_sql_user.karlcam_v2_user.name}:PASSWORD@localhost:5432/${google_sql_database.karlcam_v2.name}"
  sensitive   = false
}

output "cloud_sql_proxy_command" {
  description = "Command to start Cloud SQL proxy for local development"
  value       = "cloud-sql-proxy ${google_sql_database_instance.karlcam_db.connection_name} --port 5432 --gcloud-auth"
}