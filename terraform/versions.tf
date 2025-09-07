# KarlCam Terraform Provider Requirements

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.4"
    }
  }

  # Optional: Configure remote state backend
  # Uncomment and configure for production use
  # backend "gcs" {
  #   bucket = "karlcam-terraform-state"
  #   prefix = "terraform/state"
  # }
}

# Configure the Google Cloud Provider
provider "google" {
  project = var.project_id
  region  = var.region
}

# Configure the Google Cloud Beta Provider (for newer features)
provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Random provider for generating passwords/secrets
provider "random" {
  # Configuration options
}