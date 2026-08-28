variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
  default     = "your-gcp-project-id"
}

variable "access_token" {
  description = "OAuth 2.0 access token for GCP provider"
  type        = string
  default     = ""
}

variable "region" {
  description = "Google Cloud Region"
  type        = string
  default     = "us-central1"
}

variable "bucket_name" {
  description = "GCS Temporary Audio Storage Bucket Name"
  type        = string
  default     = "your-gcp-project-id-meet-audio-temp"
}

variable "artifact_repo_name" {
  description = "Artifact Registry Docker Repository Name"
  type        = string
  default     = "enterprise-meet-notes-repo"
}

variable "tasks_queue_name" {
  description = "Cloud Tasks Queue Name for Asynchronous Notes Generation"
  type        = string
  default     = "meet-notes-queue"
}

variable "bigquery_dataset_id" {
  description = "BigQuery Analytics Dataset ID"
  type        = string
  default     = "enterprise_portal_analytics"
}

variable "service_account_id" {
  description = "Dedicated Service Account ID for Meet Notes Processor"
  type        = string
  default     = "enterprise-meet-notes-sa"
}
