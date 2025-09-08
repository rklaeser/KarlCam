# Shared Infrastructure Variables

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "sql_instance_tier" {
  description = "The tier for the Cloud SQL instance"
  type        = string
  default     = "db-f1-micro"
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for the SQL instance"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 7
}