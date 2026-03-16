terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project               = var.project_id
  region                = var.region
  billing_project       = var.project_id
  user_project_override = true
}

# Enable Cloud Scheduler API
resource "google_project_service" "cloud_scheduler" {
  service            = "cloudscheduler.googleapis.com"
  disable_on_destroy = false
}

# Cloud SQL instance
resource "google_sql_database_instance" "main" {
  name             = "finance-tracker-db"
  database_version = "POSTGRES_15"
  region           = var.region
  deletion_protection = false

  settings {
    tier              = "db-f1-micro"  # Free tier
    availability_type = "ZONAL"
    disk_size         = 10
    disk_type         = "PD_HDD"

    database_flags {
      name  = "cloudsql.iam_authentication"
      value = "on"
    }

    backup_configuration {
      enabled = false  # Disabled for free tier
    }
  }
}

# Database
resource "google_sql_database" "database" {
  name     = "finance_tracker"
  instance = google_sql_database_instance.main.name
}

# IAM database user for Cloud Run service account
# Note: With IAM authentication enabled, the database user is created automatically
# on first connection when the service account has cloudsql.client role (granted in iam.tf)
# resource "google_sql_user" "iam_user" {
#   name     = trimsuffix(data.google_compute_default_service_account.default.email, ".gserviceaccount.com")
#   instance = google_sql_database_instance.main.name
#   type     = "CLOUD_IAM_SERVICE_ACCOUNT"
# }

# Data source for default compute service account
data "google_compute_default_service_account" "default" {}

# Cloud Scheduler: start Cloud SQL at 8am
resource "google_cloud_scheduler_job" "sql_start" {
  name             = "finance-tracker-sql-start"
  description      = "Start Cloud SQL instance at 8am"
  schedule         = "0 8 * * *"
  time_zone        = var.timezone
  attempt_deadline = "60s"
  depends_on       = [google_project_service.cloud_scheduler]

  http_target {
    http_method = "PATCH"
    uri         = "https://sqladmin.googleapis.com/sql/v1beta4/projects/${var.project_id}/instances/${google_sql_database_instance.main.name}"
    body        = base64encode(jsonencode({ settings = { activationPolicy = "ALWAYS" } }))
    headers     = { "Content-Type" = "application/json" }

    oauth_token {
      service_account_email = data.google_compute_default_service_account.default.email
    }
  }
}

# Cloud Scheduler: stop Cloud SQL at 11pm
resource "google_cloud_scheduler_job" "sql_stop" {
  name             = "finance-tracker-sql-stop"
  description      = "Stop Cloud SQL instance at 11pm"
  schedule         = "0 23 * * *"
  time_zone        = var.timezone
  attempt_deadline = "60s"
  depends_on       = [google_project_service.cloud_scheduler]

  http_target {
    http_method = "PATCH"
    uri         = "https://sqladmin.googleapis.com/sql/v1beta4/projects/${var.project_id}/instances/${google_sql_database_instance.main.name}"
    body        = base64encode(jsonencode({ settings = { activationPolicy = "NEVER" } }))
    headers     = { "Content-Type" = "application/json" }

    oauth_token {
      service_account_email = data.google_compute_default_service_account.default.email
    }
  }
}

# Firebase Auth authorized domains
# Manages the full list — must include defaults or Terraform will remove them
resource "google_identity_platform_config" "auth" {
  project = var.project_id

  authorized_domains = [
    "localhost",
    "${var.project_id}.firebaseapp.com",
    "${var.project_id}.web.app",
    var.cloud_run_domain,
  ]
}
