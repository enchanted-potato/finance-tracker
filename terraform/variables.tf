variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "timezone" {
  description = "Timezone for Cloud Scheduler jobs (e.g. Europe/Athens, America/New_York)"
  type        = string
  default     = "Europe/London"
}

variable "cloud_run_domain" {
  description = "Cloud Run service domain (e.g. finance-tracker-xxxxx-uc.a.run.app)"
  type        = string
  default     = "finance-tracker-rntookejza-uc.a.run.app"
}
