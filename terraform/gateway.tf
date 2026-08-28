# ==============================================================================
# Google Cloud Agent Gateway & Security Perimeter Architecture
# (Cloud Armor WAF, Rate Limiter, External HTTP Load Balancer, Google API Gateway)
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. Cloud Armor WAF & DoS Defense Policy
# ------------------------------------------------------------------------------
resource "google_compute_security_policy" "agent_armor_policy" {
  name        = "coway-agent-gateway-armor"
  description = "Cloud Armor WAF, Rate Limiting & DoS Defense for Coway Agent Gateway"
  project     = var.project_id

  # Rule 1: Default Allow Rule (Priority: 2147483647)
  rule {
    action   = "allow"
    priority = "2147483647"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default allow all inbound traffic"
  }

  # Rule 2: IP-based Rate Limiting & DoS Mitigation (Priority: 1000)
  # Limits each IP to 100 requests per minute; bans for 5 minutes (300s) on violation.
  rule {
    action   = "rate_based_ban"
    priority = "1000"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"
      rate_limit_threshold {
        count        = 100
        interval_sec = 60
      }
      ban_duration_sec = 300
    }
    description = "Rate Limiting: Max 100 req/min per IP, auto-ban for 5 min on exceed"
  }

  # Rule 3: OWASP Top 10 - SQL Injection Defense (Priority: 2000)
  rule {
    action   = "deny(403)"
    priority = "2000"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('sqli-v33-stable')"
      }
    }
    description = "OWASP Top 10: Block SQL injection attempts"
  }

  # Rule 4: OWASP Top 10 - Cross-Site Scripting (XSS) Defense (Priority: 2001)
  rule {
    action   = "deny(403)"
    priority = "2001"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('xss-v33-stable')"
      }
    }
    description = "OWASP Top 10: Block Cross-Site Scripting (XSS) attempts"
  }

  # Rule 5: OWASP Top 10 - Remote Code Execution (RCE) Defense (Priority: 2002)
  rule {
    action   = "deny(403)"
    priority = "2002"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('rce-v33-stable')"
      }
    }
    description = "OWASP Top 10: Block Remote Code Execution attempts"
  }

  # Rule 6: OWASP Top 10 - Local/Remote File Inclusion (LFI/RFI) Defense (Priority: 2003)
  rule {
    action   = "deny(403)"
    priority = "2003"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('lfi-v33-stable') || evaluatePreconfiguredExpr('rfi-v33-stable')"
      }
    }
    description = "OWASP Top 10: Block Local & Remote File Inclusion attempts"
  }
}

# ------------------------------------------------------------------------------
# 2. Serverless Network Endpoint Group (NEG) pointing to Cloud Run
# ------------------------------------------------------------------------------
resource "google_compute_region_network_endpoint_group" "serverless_neg" {
  name                  = "coway-meet-notes-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  project               = var.project_id

  cloud_run {
    service = "coway-meet-notes-service"
  }

  depends_on = [google_project_service.enabled_apis]
}

# ------------------------------------------------------------------------------
# 3. External HTTP(S) Backend Service with Cloud Armor WAF & Cloud CDN
# ------------------------------------------------------------------------------
resource "google_compute_backend_service" "gateway_backend_service" {
  name                  = "coway-meet-notes-backend"
  project               = var.project_id
  protocol              = "HTTP"
  port_name             = "http"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  security_policy       = google_compute_security_policy.agent_armor_policy.id
  timeout_sec           = 900 # 15 min for large audio processing

  # Google Cloud CDN Edge Caching Activation
  enable_cdn = true
  cdn_policy {
    cache_mode                   = "CACHE_ALL_STATIC"
    default_ttl                  = 86400 # 24 hours
    client_ttl                   = 3600  # 1 hour
    max_ttl                      = 604800 # 7 days
    negative_caching             = true
    serve_while_stale            = 86400
    cache_key_policy {
      include_host           = true
      include_protocol       = true
      include_query_string   = false
    }
  }

  backend {
    group = google_compute_region_network_endpoint_group.serverless_neg.id
  }

  log_config {
    enable      = true
    sample_rate = 1.0 # 100% Audit Logging
  }

  depends_on = [google_compute_security_policy.agent_armor_policy]
}

# ------------------------------------------------------------------------------
# 4. URL Map & HTTP Target Proxy
# ------------------------------------------------------------------------------
resource "google_compute_url_map" "gateway_url_map" {
  name            = "coway-meet-notes-url-map"
  project         = var.project_id
  default_service = google_compute_backend_service.gateway_backend_service.id
}

resource "google_compute_target_http_proxy" "gateway_http_proxy" {
  name    = "coway-meet-notes-http-proxy"
  project = var.project_id
  url_map = google_compute_url_map.gateway_url_map.id
}

# ------------------------------------------------------------------------------
# 5. Global Forwarding Rule (Public IPv4 External Entry Point)
# ------------------------------------------------------------------------------
resource "google_compute_global_forwarding_rule" "gateway_forwarding_rule" {
  name                  = "coway-meet-notes-forwarding-rule"
  project               = var.project_id
  target                = google_compute_target_http_proxy.gateway_http_proxy.id
  port_range            = "80"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  ip_protocol           = "TCP"
}

# ------------------------------------------------------------------------------
# 6. Google Cloud API Gateway (Managed Agent Gateway)
# ------------------------------------------------------------------------------
resource "google_api_gateway_api" "agent_api" {
  provider     = google
  api_id       = "coway-meet-agent-gateway"
  display_name = "Coway AI Agent Gateway API"
  project      = var.project_id

  depends_on = [google_project_service.enabled_apis]
}

resource "google_api_gateway_api_config" "agent_api_cfg" {
  provider      = google
  api           = google_api_gateway_api.agent_api.api_id
  api_config_id_prefix = "coway-cfg-"
  display_name  = "Coway Agent Gateway OpenAPI Config"
  project       = var.project_id

  openapi_documents {
    document {
      path     = "openapi2-run.yaml"
      contents = filebase64("${path.module}/../openapi2-run.yaml")
    }
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [google_api_gateway_api.agent_api]
}

resource "google_api_gateway_gateway" "agent_gateway" {
  provider   = google
  gateway_id = "coway-meet-gateway"
  api_config = google_api_gateway_api_config.agent_api_cfg.id
  region     = var.region
  project    = var.project_id

  depends_on = [google_api_gateway_api_config.agent_api_cfg]
}

# IAM: Grant Cloud Run Invoker Role to the Agent Gateway Service Account / Public
resource "google_cloud_run_service_iam_member" "cloud_run_invoker" {
  location = var.region
  project  = var.project_id
  service  = "coway-meet-notes-service"
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ------------------------------------------------------------------------------
# 7. Outputs for External Access
# ------------------------------------------------------------------------------
output "public_load_balancer_ip" {
  description = "Public External IPv4 address for Cloud Armor WAF & Load Balancer"
  value       = google_compute_global_forwarding_rule.gateway_forwarding_rule.ip_address
}

output "public_http_url" {
  description = "Public HTTP URL for testing via Load Balancer"
  value       = "http://${google_compute_global_forwarding_rule.gateway_forwarding_rule.ip_address}"
}

output "api_gateway_hostname" {
  description = "Google Cloud API Gateway Default Hostname"
  value       = google_api_gateway_gateway.agent_gateway.default_hostname
}

output "api_gateway_url" {
  description = "Google Cloud API Gateway Public Live URL"
  value       = "https://${google_api_gateway_gateway.agent_gateway.default_hostname}"
}
