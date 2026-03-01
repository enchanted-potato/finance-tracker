variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "cloud_run_domain" {
  description = "Cloud Run service domain (e.g. finance-tracker-xxxxx-uc.a.run.app)"
  type        = string
  default     = "finance-tracker-rntookejza-uc.a.run.app"
}
