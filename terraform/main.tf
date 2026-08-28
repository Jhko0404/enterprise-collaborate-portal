# ==============================================================================
# 1. Google Cloud APIs Activation
# ==============================================================================
locals {
  services = [
    "aiplatform.googleapis.com",       # Vertex AI
    "storage.googleapis.com",          # Cloud Storage
    "run.googleapis.com",              # Cloud Run
    "cloudtasks.googleapis.com",       # Cloud Tasks Queue
    "bigquery.googleapis.com",         # BigQuery
    "secretmanager.googleapis.com",    # Secret Manager
    "drive.googleapis.com",            # Google Drive API
    "calendar-json.googleapis.com",    # Google Calendar API
    "docs.googleapis.com",             # Google Docs API
    "artifactregistry.googleapis.com", # Artifact Registry
    "compute.googleapis.com",          # Compute Engine & Load Balancing
    "apigateway.googleapis.com",       # API Gateway / Agent Gateway
    "servicecontrol.googleapis.com",   # Service Control
    "servicemanagement.googleapis.com" # Service Management
  ]
}

resource "google_project_service" "enabled_apis" {
  for_each                   = toset(locals.services)
  project                    = var.project_id
  service                    = each.key
  disable_dependent_services = false
  disable_on_destroy         = false
}

# ==============================================================================
# 2. Cloud Storage (GCS) Temporary Audio Bucket
# ==============================================================================
resource "google_storage_bucket" "temp_audio_bucket" {
  name                        = var.bucket_name
  location                    = "US-CENTRAL1"
  project                     = var.project_id
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  force_destroy               = true

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 1 # 1-day TTL for audio privacy and storage cleanup
    }
  }

  cors {
    origin          = ["*"]
    method          = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  depends_on = [google_project_service.enabled_apis]
}

# ==============================================================================
# 3. Artifact Registry Docker Repository
# ==============================================================================
resource "google_artifact_registry_repository" "docker_repo" {
  provider      = google
  project       = var.project_id
  location      = var.region
  repository_id = var.artifact_repo_name
  description   = "Docker repository for Coway Meet Notes AI Processor"
  format        = "DOCKER"

  depends_on = [google_project_service.enabled_apis]
}

# ==============================================================================
# 4. Cloud Tasks Asynchronous Queue
# ==============================================================================
resource "google_cloud_tasks_queue" "meeting_notes_queue" {
  name     = var.tasks_queue_name
  location = var.region
  project  = var.project_id

  rate_limits {
    max_dispatches_per_second = 20
    max_concurrent_dispatches = 10
  }

  retry_config {
    max_attempts       = 3
    min_backoff        = "2s"
    max_backoff        = "30s"
    max_doublings      = 3
    max_retry_duration = "600s"
  }

  depends_on = [google_project_service.enabled_apis]
}

# ==============================================================================
# 5. BigQuery Dataset & Analytics Tables
# ==============================================================================
resource "google_bigquery_dataset" "portal_analytics" {
  dataset_id                  = var.bigquery_dataset_id
  friendly_name               = "Coway Portal AI Analytics"
  description                 = "Dataset for audit logs and user feedback on AI Meeting Notes"
  location                    = "US"
  project                     = var.project_id
  default_table_expiration_ms = null

  depends_on = [google_project_service.enabled_apis]
}

# Audit Logs Table
resource "google_bigquery_table" "audit_logs" {
  dataset_id          = google_bigquery_dataset.portal_analytics.dataset_id
  table_id            = "meeting_ai_audit_logs"
  project             = var.project_id
  description         = "Audit logs for AI meeting note generation jobs"
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "created_at"
  }

  clustering = ["template_type", "execution_status"]

  schema = <<EOF
[
  {"name": "trace_id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "job_id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "requestor_email", "type": "STRING", "mode": "REQUIRED"},
  {"name": "meeting_title", "type": "STRING", "mode": "NULLABLE"},
  {"name": "audio_duration_seconds", "type": "INT64", "mode": "NULLABLE"},
  {"name": "audio_file_size_bytes", "type": "INT64", "mode": "NULLABLE"},
  {"name": "template_type", "type": "STRING", "mode": "NULLABLE"},
  {"name": "vertex_model_name", "type": "STRING", "mode": "NULLABLE"},
  {"name": "audio_tokens_used", "type": "INT64", "mode": "NULLABLE"},
  {"name": "output_tokens_used", "type": "INT64", "mode": "NULLABLE"},
  {"name": "execution_status", "type": "STRING", "mode": "REQUIRED"},
  {"name": "total_latency_ms", "type": "INT64", "mode": "REQUIRED"},
  {"name": "audio_extract_latency_ms", "type": "INT64", "mode": "NULLABLE"},
  {"name": "gemini_latency_ms", "type": "INT64", "mode": "NULLABLE"},
  {"name": "docs_create_latency_ms", "type": "INT64", "mode": "NULLABLE"},
  {"name": "created_at", "type": "TIMESTAMP", "mode": "REQUIRED"}
]
EOF

  depends_on = [google_bigquery_dataset.portal_analytics]
}

# Feedback Table
resource "google_bigquery_table" "feedback" {
  dataset_id          = google_bigquery_dataset.portal_analytics.dataset_id
  table_id            = "meeting_notes_feedback"
  project             = var.project_id
  description         = "User CSAT and feedback on generated meeting notes"
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "created_at"
  }

  clustering = ["template_type", "rating_score"]

  schema = <<EOF
[
  {"name": "feedback_id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "job_id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "requestor_email", "type": "STRING", "mode": "REQUIRED"},
  {"name": "template_type", "type": "STRING", "mode": "REQUIRED"},
  {"name": "rating_score", "type": "INT64", "mode": "NULLABLE"},
  {"name": "is_diarization_accurate", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "is_summary_accurate", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "user_comment", "type": "STRING", "mode": "NULLABLE"},
  {"name": "created_at", "type": "TIMESTAMP", "mode": "REQUIRED"}
]
EOF

  depends_on = [google_bigquery_dataset.portal_analytics]
}

# ==============================================================================
# 6. Dedicated Service Account & IAM Roles
# ==============================================================================
resource "google_service_account" "processor_sa" {
  account_id   = var.service_account_id
  display_name = "Coway Meet Notes AI Processor Service Account"
  project      = var.project_id

  depends_on = [google_project_service.enabled_apis]
}

locals {
  sa_roles = [
    "roles/aiplatform.user",
    "roles/bigquery.dataEditor",
    "roles/cloudtasks.enqueuer",
  ]
}

resource "google_project_iam_member" "sa_role_bindings" {
  for_each = toset(locals.sa_roles)
  project  = var.project_id
  role     = each.key
  member   = "serviceAccount:${google_service_account.processor_sa.email}"
}

# Storage Bucket Object Admin for the temp bucket
resource "google_storage_bucket_iam_member" "sa_bucket_admin" {
  bucket = google_storage_bucket.temp_audio_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.processor_sa.email}"
}
