# Grant Cloud SQL Client role to Cloud Run service account
resource "google_project_iam_member" "cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${data.google_compute_default_service_account.default.email}"
}

# Grant Cloud SQL Editor role so the scheduler can start/stop the instance
resource "google_project_iam_member" "cloudsql_editor" {
  project = var.project_id
  role    = "roles/cloudsql.editor"
  member  = "serviceAccount:${data.google_compute_default_service_account.default.email}"
}

# Allow Cloud Scheduler service agent to generate tokens for the default SA
data "google_project" "project" {}

resource "google_service_account_iam_member" "scheduler_token_creator" {
  service_account_id = data.google_compute_default_service_account.default.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-cloudscheduler.iam.gserviceaccount.com"
  depends_on         = [google_project_service.cloud_scheduler]
}

