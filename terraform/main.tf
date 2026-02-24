terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
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
resource "google_sql_user" "iam_user" {
  name     = data.google_compute_default_service_account.default.email
  instance = google_sql_database_instance.main.name
  type     = "CLOUD_IAM_SERVICE_ACCOUNT"
}

# Data source for default compute service account
data "google_compute_default_service_account" "default" {}
