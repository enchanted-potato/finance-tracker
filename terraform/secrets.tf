# Secret Manager secret for Firebase credentials
resource "google_secret_manager_secret" "firebase_creds" {
  secret_id = "finance-tracker-firebase-creds"

  replication {
    auto {}
  }
}

# Secret version with Firebase credentials
resource "google_secret_manager_secret_version" "firebase_creds_version" {
  secret      = google_secret_manager_secret.firebase_creds.id
  secret_data = file("${path.root}/../.firebase/firebase-tracker-sa.json")
}
