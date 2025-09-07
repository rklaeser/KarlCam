# KarlCam Terraform Variables

variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
  default     = "karlcam"
}

variable "region" {
  description = "Google Cloud region for resources"
  type        = string
  default     = "us-central1"
}

variable "bucket_name" {
  description = "Cloud Storage bucket name for KarlCam data"
  type        = string
  default     = "karlcam-v2-data"
}

variable "database_password" {
  description = "Password for the KarlCam database user"
  type        = string
  sensitive   = true
}

variable "gemini_api_key" {
  description = "API key for Google Gemini AI service"
  type        = string
  sensitive   = true
}

variable "domain" {
  description = "Domain name for KarlCam (without subdomains)"
  type        = string
  default     = "karl.cam"
}

variable "api_subdomain" {
  description = "Subdomain for API service"
  type        = string
  default     = "api"
}

variable "admin_subdomain" {
  description = "Subdomain for admin interface"
  type        = string
  default     = "admin"
}

variable "admin_api_subdomain" {
  description = "Subdomain for admin API"
  type        = string
  default     = "admin-api"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for critical resources"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Number of days to retain database backups"
  type        = number
  default     = 7
  
  validation {
    condition     = var.backup_retention_days >= 1 && var.backup_retention_days <= 365
    error_message = "Backup retention days must be between 1 and 365."
  }
}

variable "max_api_instances" {
  description = "Maximum number of API service instances"
  type        = number
  default     = 10
}

variable "max_frontend_instances" {
  description = "Maximum number of frontend service instances"
  type        = number
  default     = 5
}

variable "max_admin_instances" {
  description = "Maximum number of admin service instances"
  type        = number
  default     = 3
}

variable "collector_schedule" {
  description = "Cron schedule for the collector job"
  type        = string
  default     = "0 */4 * * *"  # Every 4 hours
}

variable "labeler_schedule" {
  description = "Cron schedule for the labeler job"
  type        = string
  default     = "30 2 * * *"   # Daily at 2:30 AM
}