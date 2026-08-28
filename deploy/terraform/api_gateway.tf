# 4. API Gateway 리소스 및 Config
resource "google_api_gateway_api" "api" {
  provider     = google
  api_id       = var.api_id
  display_name = "Enterprise Collaborate Portal Agent API"
  depends_on   = [google_project_service.apis]
}

resource "google_api_gateway_api_config" "api_cfg" {
  provider      = google
  api           = google_api_gateway_api.api.api_id
  api_config_id = "ent-cfg-v1"
  display_name  = "Enterprise Agent API Config v1"

  openapi_documents {
    document {
      path = "openapi2-agentgateway.yaml"
      contents = base64encode(
        replace(
          file("${path.module}/../openapi2-agentgateway.yaml"),
          "$${BACKEND_CLOUD_RUN_URL}",
          google_cloud_run_v2_service.backend.uri
        )
      )
    }
  }

  gateway_backend_service_account = google_service_account.gateway_sa.email

  lifecycle {
    create_before_destroy = true
  }
}

resource "google_api_gateway_gateway" "gateway" {
  provider   = google
  gateway_id = var.gateway_id
  api_config = google_api_gateway_api_config.api_cfg.id
  region     = var.region
  depends_on = [google_api_gateway_api_config.api_cfg]
}
