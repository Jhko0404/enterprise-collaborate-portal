# 1. Cloud Run 백엔드 (Zero-Trust: 미인증 접근 차단)
resource "google_cloud_run_v2_service" "backend" {
  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = "gcr.io/${var.project_id}/${var.service_name}:latest"

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "GCP_LOCATION"
        value = var.region
      }
      env {
        name  = "GEMINI_MODEL_NAME"
        value = "gemini-3.7-flash"
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
    timeout = "600s"
  }

  depends_on = [google_project_service.apis]
}
