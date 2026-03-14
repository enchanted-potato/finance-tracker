output "instance_connection_name" {
  description = "Cloud SQL instance connection name"
  value       = google_sql_database_instance.main.connection_name
}

output "service_account_email" {
  description = "Cloud Run default service account email"
  value       = data.google_compute_default_service_account.default.email
}

output "database_name" {
  description = "Database name"
  value       = google_sql_database.database.name
}
