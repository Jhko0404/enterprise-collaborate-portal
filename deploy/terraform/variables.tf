variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "your-gcp-project-id"
}

variable "region" {
  description = "GCP Region for Cloud Run and API Gateway"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Cloud Run backend service name"
  type        = string
  default     = "enterprise-meet-notes-service"
}

variable "gateway_id" {
  description = "API Gateway ID"
  type        = string
  default     = "enterprise-agent-gateway"
}

variable "api_id" {
  description = "API Gateway API ID"
  type        = string
  default     = "enterprise-agent-api"
}
