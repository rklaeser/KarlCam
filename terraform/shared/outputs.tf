# Shared Infrastructure Outputs

output "sql_instance_name" {
  description = "The name of the Cloud SQL instance"
  value       = google_sql_database_instance.karlcam_db.name
}

output "sql_instance_connection_name" {
  description = "The connection name of the Cloud SQL instance"
  value       = google_sql_database_instance.karlcam_db.connection_name
}

output "service_account_email" {
  description = "Email address of the backend service account"
  value       = google_service_account.karlcam_backend.email
}

output "project_apis" {
  description = "Enabled project APIs"
  value       = google_project_service.required_apis
}

output "staging_database_name" {
  description = "Name of the staging database"
  value       = google_sql_database.karlcam_staging.name
}

output "production_database_name" {
  description = "Name of the production database" 
  value       = google_sql_database.karlcam_production.name
}