# KarlCam Terraform Infrastructure

This directory contains Terraform configuration files for deploying KarlCam's infrastructure on Google Cloud Platform.

## 🚀 Why Terraform Over Bash Scripts?

### Reliability Benefits

- **Declarative Infrastructure**: Define what you want, not how to get there
- **State Management**: Terraform tracks what exists vs. what should exist
- **Idempotency**: Safe to run multiple times without creating duplicates
- **Plan & Preview**: See exactly what changes before applying them
- **Rollback Capability**: Revert to previous working configurations
- **Resource Dependencies**: Automatic ordering of resource creation/updates
- **Drift Detection**: Identify manual changes made outside of Terraform

### Operational Benefits

- **Consistent Deployments**: Same result every time
- **Environment Parity**: Identical staging/production setups
- **Disaster Recovery**: Recreate entire infrastructure from code
- **Change Management**: All infrastructure changes tracked in version control
- **Team Collaboration**: Infrastructure as code enables team workflows

## 📁 File Structure

```
terraform/
├── main.tf           # Core infrastructure (Cloud SQL, Storage, IAM)
├── cloud-run.tf      # Cloud Run services and jobs
├── variables.tf      # Input variables and configuration
├── outputs.tf        # Export important values and commands
├── versions.tf       # Provider versions and requirements
├── secrets.tf        # Secret Manager resources
├── networking.tf     # Domain mappings and networking
└── README.md         # This file
```

## 🔧 Prerequisites

1. **Google Cloud Setup**:
   ```bash
   # Install gcloud CLI
   # Authenticate
   gcloud auth login
   gcloud auth application-default login
   
   # Set project
   gcloud config set project karlcam
   ```

2. **Terraform Installation**:
   ```bash
   # macOS
   brew install terraform
   
   # Or download from https://terraform.io/downloads
   ```

3. **Required Secrets**:
   - Gemini API key
   - Database password (or let Terraform generate one)

## 🚀 Quick Start

### 1. Create Variable File

Create `terraform.tfvars` with your configuration:

```hcl
# terraform.tfvars
project_id        = "karlcam"
region           = "us-central1"
bucket_name      = "karlcam-v2-data"
domain           = "karl.cam"

# Secrets (keep secure!)
database_password = "your-secure-db-password"
gemini_api_key    = "your-gemini-api-key"

# Optional customizations
environment                = "prod"
max_api_instances         = 10
max_frontend_instances    = 5
collector_schedule        = "0 */4 * * *"  # Every 4 hours
```

### 2. Initialize Terraform

```bash
cd terraform
terraform init
```

### 3. Plan Deployment

```bash
terraform plan
```

This shows you exactly what will be created before making any changes.

### 4. Apply Configuration

```bash
terraform apply
```

Review the plan and type `yes` to proceed.

## 🔄 Common Operations

### View Current State
```bash
terraform show
```

### Update Infrastructure
```bash
# Make changes to .tf files
terraform plan    # Preview changes
terraform apply   # Apply changes
```

### Check for Drift
```bash
terraform plan -detailed-exitcode
```

### Import Existing Resources
If you have existing resources created by bash scripts:

```bash
# Example: Import existing Cloud SQL instance
terraform import google_sql_database_instance.karlcam_db karlcam/karlcam-db

# Import Cloud Storage bucket
terraform import google_storage_bucket.karlcam_data karlcam-v2-data
```

### Rollback Changes
```bash
# Revert to previous state file backup
terraform apply -state=terraform.tfstate.backup
```

## 🌍 Environment Management

### Development Environment
Create `dev.tfvars`:

```hcl
project_id = "karlcam-dev"
environment = "dev"
bucket_name = "karlcam-dev-data"
max_api_instances = 2
max_frontend_instances = 1
```

Deploy with:
```bash
terraform apply -var-file="dev.tfvars"
```

### Production vs Development
```bash
# Production
terraform workspace new prod
terraform apply -var-file="prod.tfvars"

# Development  
terraform workspace new dev
terraform apply -var-file="dev.tfvars"
```

## 🔐 Security Best Practices

### Store Sensitive Variables Securely

**Option 1: Environment Variables**
```bash
export TF_VAR_database_password="your-password"
export TF_VAR_gemini_api_key="your-api-key"
terraform apply
```

**Option 2: Terraform Cloud/Enterprise**
Store sensitive variables in Terraform Cloud workspace.

**Option 3: External Secrets**
```bash
# Use gcloud to fetch secrets
terraform apply \
  -var="database_password=$(gcloud secrets versions access latest --secret=karlcam-db-password)" \
  -var="gemini_api_key=$(gcloud secrets versions access latest --secret=gemini-api-key)"
```

### Remote State Backend
For production, use remote state storage:

```hcl
# In versions.tf
terraform {
  backend "gcs" {
    bucket = "karlcam-terraform-state"
    prefix = "terraform/state"
  }
}
```

## 📊 Monitoring and Maintenance

### Check Resource Status
```bash
# View all outputs
terraform output

# Specific output
terraform output api_service_url
```

### Manual Operations
```bash
# Run collector job
$(terraform output -raw collector_run_command)

# View API logs
$(terraform output -raw api_logs_command)

# Connect to database locally
$(terraform output -raw cloud_sql_proxy_command)
```

## 🚨 Troubleshooting

### Common Issues

**1. Domain Mapping Failures**
- Verify DNS records are configured correctly
- Check domain ownership in Google Search Console

**2. Permission Errors**
- Ensure service account has required roles
- Check IAM policy bindings

**3. Resource Already Exists**
- Use `terraform import` to bring existing resources under management
- Or rename resources in Terraform to avoid conflicts

**4. State File Issues**
```bash
# Refresh state from actual infrastructure
terraform refresh

# Remove resource from state (without destroying)
terraform state rm google_cloud_run_service.example

# Move resource in state
terraform state mv old_name new_name
```

### Debugging
```bash
# Enable detailed logging
export TF_LOG=DEBUG
terraform apply

# Validate configuration
terraform validate

# Format code
terraform fmt -recursive
```

## 🔄 Migration from Bash Scripts

### Phase 1: Import Existing Resources
1. List current resources: `gcloud run services list`
2. Import each resource: `terraform import ...`
3. Run `terraform plan` to verify no changes

### Phase 2: Gradual Replacement
1. Start with new resources (jobs, secrets)
2. Gradually move services under Terraform management
3. Retire bash scripts once everything is imported

### Phase 3: Enhanced Reliability
1. Add monitoring and alerting resources
2. Implement blue-green deployments
3. Add automated testing and validation

## 📈 Advanced Features

### Auto-scaling Configuration
```hcl
# In cloud-run.tf, modify service templates:
scaling {
  min_instance_count = 0
  max_instance_count = var.max_api_instances
}
```

### Monitoring and Alerting
Add to a new `monitoring.tf` file:

```hcl
resource "google_monitoring_alert_policy" "api_error_rate" {
  display_name = "KarlCam API Error Rate"
  combiner     = "OR"
  
  conditions {
    display_name = "API Error Rate > 5%"
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05
      duration        = "300s"
    }
  }
}
```

### Blue-Green Deployments
```hcl
# Use traffic splitting
resource "google_cloud_run_service" "karlcam_api" {
  # ... existing config ...
  
  traffic {
    percent         = 90
    revision_name   = "${google_cloud_run_service.karlcam_api.metadata[0].name}-blue"
  }
  
  traffic {
    percent         = 10
    revision_name   = "${google_cloud_run_service.karlcam_api.metadata[0].name}-green"
  }
}
```

## 🤝 Contributing

1. Make changes to `.tf` files
2. Run `terraform fmt` to format code
3. Run `terraform validate` to check syntax
4. Run `terraform plan` to preview changes
5. Submit PR with plan output

## 📚 References

- [Terraform Google Provider Docs](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Google Cloud Run Terraform Examples](https://cloud.google.com/run/docs/configuring/services)
- [Terraform Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/index.html)