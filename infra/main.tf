terraform {
  required_version = ">= 1.6, < 2.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  type        = string
  description = "Existing billing-enabled project approved for this watcher. Prefer a dedicated project."
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "image" {
  type        = string
  default     = ""
  description = "Empty provisions prerequisites only. Then set the built image URI pinned by @sha256 digest."
  validation {
    condition     = var.image == "" || can(regex("@sha256:[a-f0-9]{64}$", var.image))
    error_message = "Deploy an immutable image digest, not a mutable tag."
  }
}

variable "scheduler_paused" {
  type        = bool
  default     = true
  description = "Keep paused until baseline import, secrets, manual smoke check, and watchdog setup are complete."
}

locals {
  name = "imax-watcher"
  apis = toset([
    "run.googleapis.com", "cloudscheduler.googleapis.com", "firestore.googleapis.com",
    "secretmanager.googleapis.com", "artifactregistry.googleapis.com", "cloudbuild.googleapis.com",
    "iam.googleapis.com", "cloudresourcemanager.googleapis.com",
  ])
  deployed = var.image == "" ? 0 : 1
}

resource "google_project_service" "api" {
  for_each           = local.apis
  service            = each.key
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "images" {
  location      = var.region
  repository_id = local.name
  format        = "DOCKER"
  depends_on    = [google_project_service.api]
}

resource "google_service_account" "runtime" {
  account_id   = "imax-watcher-runtime"
  display_name = "IMAX watcher runtime"
  depends_on   = [google_project_service.api]
}

resource "google_service_account" "scheduler" {
  account_id   = "imax-watcher-scheduler"
  display_name = "IMAX watcher invoker only"
  depends_on   = [google_project_service.api]
}

resource "google_firestore_database" "state" {
  project                   = var.project_id
  name                      = local.name
  location_id               = var.region
  type                      = "FIRESTORE_NATIVE"
  delete_protection_state = "DELETE_PROTECTION_ENABLED"
  depends_on                = [google_project_service.api]
}

resource "google_firestore_field" "unindexed_state" {
  project    = var.project_id
  database   = google_firestore_database.state.name
  collection = "watcher_states"
  field      = "state_json"
  index_config {}
}

resource "google_project_iam_member" "state_access" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

# Secret VALUES are deliberately not created by Terraform or checked into git.
# Add versions securely before setting var.image to deploy the service.
resource "google_secret_manager_secret" "secret" {
  for_each  = toset(["imax-ntfy-topic", "imax-healthchecks-ping"])
  secret_id = each.key
  replication {
    auto {}
  }
  depends_on = [google_project_service.api]
}

resource "google_secret_manager_secret_iam_member" "secret_access" {
  for_each  = google_secret_manager_secret.secret
  secret_id = each.value.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_cloud_run_v2_service" "watcher" {
  count               = local.deployed
  name                = local.name
  location            = var.region
  deletion_protection = true
  ingress             = "INGRESS_TRAFFIC_ALL" # Still PRIVATE: IAM has no allUsers grant.
  template {
    service_account                  = google_service_account.runtime.email
    timeout                          = "330s"
    max_instance_request_concurrency = 1
    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }
    containers {
      image = var.image
      ports {
        container_port = 8080
      }
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "FIRESTORE_DATABASE"
        value = google_firestore_database.state.name
      }
      env {
        name  = "EXPECTED_SCHEDULER_JOB"
        value = "projects/${var.project_id}/locations/${var.region}/jobs/${local.name}"
      }
      env {
        name  = "NTFY_SERVER"
        value = "https://ntfy.sh"
      }
      env {
        name = "NTFY_TOPIC"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secret["imax-ntfy-topic"].secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "HC_PING_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secret["imax-healthchecks-ping"].secret_id
            version = "latest"
          }
        }
      }
      startup_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 0
        timeout_seconds       = 2
        period_seconds        = 3
        failure_threshold     = 10
      }
    }
  }
  depends_on = [google_secret_manager_secret_iam_member.secret_access, google_project_iam_member.state_access]
}

resource "google_cloud_run_v2_service_iam_member" "invoke" {
  count    = local.deployed
  name     = google_cloud_run_v2_service.watcher[0].name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}

resource "google_cloud_scheduler_job" "watch" {
  count            = local.deployed
  name             = local.name
  region           = var.region
  schedule         = "*/10 * * * *"
  time_zone        = "Etc/UTC"
  paused           = var.scheduler_paused
  attempt_deadline = "360s"
  retry_config {
    retry_count          = 1
    max_retry_duration   = "300s"
    min_backoff_duration = "30s"
    max_backoff_duration = "30s"
    max_doublings        = 0
  }
  http_target {
    uri         = "${google_cloud_run_v2_service.watcher[0].uri}/run"
    http_method = "POST"
    oidc_token {
      service_account_email = google_service_account.scheduler.email
      audience              = google_cloud_run_v2_service.watcher[0].uri
    }
  }
  depends_on = [google_cloud_run_v2_service_iam_member.invoke]
}

output "image_repository" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${local.name}/watcher"
}

output "service_url" {
  value = try(google_cloud_run_v2_service.watcher[0].uri, null)
}

output "scheduler_service_account" {
  value = google_service_account.scheduler.email
}
