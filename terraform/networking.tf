# KarlCam Networking and Domain Configuration

# Domain mapping for main frontend (karl.cam)
resource "google_cloud_run_domain_mapping" "frontend" {
  location = var.region
  name     = var.domain
  project  = var.project_id

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_v2_service.karlcam_frontend.name
  }

  depends_on = [google_cloud_run_v2_service.karlcam_frontend]
}

# Domain mapping for API (api.karl.cam)
resource "google_cloud_run_domain_mapping" "api" {
  location = var.region
  name     = "${var.api_subdomain}.${var.domain}"
  project  = var.project_id

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_v2_service.karlcam_api.name
  }

  depends_on = [google_cloud_run_v2_service.karlcam_api]
}

# Domain mapping for admin frontend (admin.karl.cam)
resource "google_cloud_run_domain_mapping" "admin_frontend" {
  location = var.region
  name     = "${var.admin_subdomain}.${var.domain}"
  project  = var.project_id

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_v2_service.karlcam_admin_frontend.name
  }

  depends_on = [google_cloud_run_v2_service.karlcam_admin_frontend]
}

# Domain mapping for admin API (admin-api.karl.cam)
resource "google_cloud_run_domain_mapping" "admin_api" {
  location = var.region
  name     = "${var.admin_api_subdomain}.${var.domain}"
  project  = var.project_id

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_v2_service.karlcam_admin_backend.name
  }

  depends_on = [google_cloud_run_v2_service.karlcam_admin_backend]
}

# Optional: Global Load Balancer for HTTPS and CDN
# Uncomment if you want to use a global load balancer instead of Cloud Run domain mappings

# resource "google_compute_global_address" "karlcam_ip" {
#   name         = "karlcam-global-ip"
#   project      = var.project_id
#   address_type = "EXTERNAL"
# }

# resource "google_compute_managed_ssl_certificate" "karlcam_ssl" {
#   name    = "karlcam-ssl-cert"
#   project = var.project_id

#   managed {
#     domains = [
#       var.domain,
#       "${var.api_subdomain}.${var.domain}",
#       "${var.admin_subdomain}.${var.domain}",
#       "${var.admin_api_subdomain}.${var.domain}"
#     ]
#   }
# }

# # Network Endpoint Group for Cloud Run services
# resource "google_compute_region_network_endpoint_group" "karlcam_neg" {
#   for_each = {
#     api            = google_cloud_run_v2_service.karlcam_api.uri
#     frontend       = google_cloud_run_v2_service.karlcam_frontend.uri
#     admin_backend  = google_cloud_run_v2_service.karlcam_admin_backend.uri
#     admin_frontend = google_cloud_run_v2_service.karlcam_admin_frontend.uri
#   }

#   name                  = "karlcam-${each.key}-neg"
#   project               = var.project_id
#   network_endpoint_type = "SERVERLESS"
#   region                = var.region

#   cloud_run {
#     service = each.key == "api" ? google_cloud_run_v2_service.karlcam_api.name : (
#       each.key == "frontend" ? google_cloud_run_v2_service.karlcam_frontend.name : (
#         each.key == "admin_backend" ? google_cloud_run_v2_service.karlcam_admin_backend.name :
#         google_cloud_run_v2_service.karlcam_admin_frontend.name
#       )
#     )
#   }
# }

# Output the required DNS records
output "dns_records_required" {
  description = "DNS records that need to be configured for domain mappings"
  value = {
    "${var.domain}" = {
      type  = "A"
      value = "216.239.32.21,216.239.34.21,216.239.36.21,216.239.38.21"
      note  = "Google Cloud Run IP addresses for domain mapping"
    }
    "${var.api_subdomain}.${var.domain}" = {
      type  = "A"
      value = "216.239.32.21,216.239.34.21,216.239.36.21,216.239.38.21"
      note  = "Google Cloud Run IP addresses for domain mapping"
    }
    "${var.admin_subdomain}.${var.domain}" = {
      type  = "A"
      value = "216.239.32.21,216.239.34.21,216.239.36.21,216.239.38.21"
      note  = "Google Cloud Run IP addresses for domain mapping"
    }
    "${var.admin_api_subdomain}.${var.domain}" = {
      type  = "A"
      value = "216.239.32.21,216.239.34.21,216.239.36.21,216.239.38.21"
      note  = "Google Cloud Run IP addresses for domain mapping"
    }
  }
}

# Output domain mapping status
output "domain_mapping_status" {
  description = "Status of domain mappings (check after applying)"
  value = {
    frontend_domain    = google_cloud_run_domain_mapping.frontend.name
    api_domain        = google_cloud_run_domain_mapping.api.name
    admin_domain      = google_cloud_run_domain_mapping.admin_frontend.name
    admin_api_domain  = google_cloud_run_domain_mapping.admin_api.name
  }
}