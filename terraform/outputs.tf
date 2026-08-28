output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "temp_audio_bucket_url" {
  description = "GCS Temporary Audio Bucket URL"
  value       = google_storage_bucket.temp_audio_bucket.url
}

output "docker_repository_id" {
  description = "Artifact Registry Docker Repository ID"
  value       = google_artifact_registry_repository.docker_repo.id
}

output "cloud_tasks_queue_id" {
  description = "Cloud Tasks Queue ID"
  value       = google_cloud_tasks_queue.meeting_notes_queue.id
}

output "bigquery_dataset_id" {
  description = "BigQuery Analytics Dataset ID"
  value       = google_bigquery_dataset.portal_analytics.dataset_id
}

output "service_account_email" {
  description = "Dedicated Service Account Email"
  value       = google_service_account.processor_sa.email
}
