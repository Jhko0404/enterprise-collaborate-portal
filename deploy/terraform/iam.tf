# 2. API Gateway 전용 서비스 계정
resource "google_service_account" "gateway_sa" {
  account_id   = "agent-gateway-sa"
  display_name = "Agent Gateway Ingress Service Account"
}

# 3. Cloud Run Invoker 권한 바인딩 (오직 게이트웨이만 백엔드 호출 가능)
resource "google_cloud_run_service_iam_member" "invoker" {
  location = var.region
  service  = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.gateway_sa.email}"
}
