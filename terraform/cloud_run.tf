# ==============================================================================
# Cloud Run Service for Coway AI Meeting Notes Processor
# ==============================================================================
resource "google_cloud_run_v2_service" "meet_notes_service" {
  name     = "coway-meet-notes-service"
  location = var.region
  project  = var.project_id
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER" # Company Security Org Policy

  template {
    service_account = google_service_account.processor_sa.email
    timeout         = "900s"

    scaling {
      min_instance_count = 0
      max_instance_count = 100
    }

    containers {
      image = "us-central1-docker.pkg.dev/${var.project_id}/cloud-run-source-deploy/coway-meet-notes-service:latest"

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
        name  = "TEMP_GCS_BUCKET"
        value = google_storage_bucket.temp_audio_bucket.name
      }
      env {
        name  = "GEMINI_MODEL_NAME"
        value = "gemini-3.7-flash"
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_project_service.enabled_apis,
    google_service_account.processor_sa,
    google_storage_bucket.temp_audio_bucket
  ]
}

output "cloud_run_service_url" {
  description = "Deployed Cloud Run Service Live URL"
  value       = google_cloud_run_v2_service.meet_notes_service.uri
}
