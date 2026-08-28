output "cloud_run_backend_url" {
  description = "내부 Cloud Run 백엔드 URL"
  value       = google_cloud_run_v2_service.backend.uri
}

output "agent_gateway_public_url" {
  description = "외부에서 접근 가능한 공용 Agent Gateway URL"
  value       = "https://${google_api_gateway_gateway.gateway.default_hostname}"
}

output "gateway_service_account" {
  description = "게이트웨이 OIDC 서비스 계정"
  value       = google_service_account.gateway_sa.email
}
