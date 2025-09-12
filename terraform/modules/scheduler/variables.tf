# Scheduler Module Variables

variable "environment" {
  description = "Environment name (staging, production)"
  type        = string
}

variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud region"
  type        = string
}


variable "pipeline_schedule" {
  description = "Cron schedule for the unified pipeline job"
  type        = string
}

variable "pipeline_job_name" {
  description = "Name of the unified pipeline Cloud Run job"
  type        = string
}

variable "service_account_email" {
  description = "Service account email for scheduler"
  type        = string
}