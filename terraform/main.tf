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

# Firebase Hosting site — required for signInWithRedirect auth handler
# The /__/auth/handler page is served by Firebase Hosting
resource "google_firebase_hosting_site" "default" {
  provider = google
  project  = var.project_id
  site_id  = var.project_id
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
