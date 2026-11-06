terraform {
  required_version = ">= 1.11, < 2.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "8.10.0"
    }
  }
}

# Configuração exclusivamente local: sem ADC, chaves ou endpoints reais.
provider "google" {
  project                 = "cloudops-local"
  region                  = "us-central1"
  access_token            = "local-emulator-only"
  storage_custom_endpoint = "http://127.0.0.1:4588/storage/v1/"
  pubsub_custom_endpoint  = "http://127.0.0.1:4588/v1/"
  user_project_override   = false
}

resource "google_storage_bucket" "orders" {
  name                        = "cloudops-local-orders"
  location                    = "US"
  uniform_bucket_level_access = true
  force_destroy               = false
}

resource "google_pubsub_topic" "orders" {
  name = "orders"
}

resource "google_pubsub_subscription" "orders" {
  name                 = "order-worker"
  topic                = google_pubsub_topic.orders.id
  ack_deadline_seconds = 30
}

output "bucket" {
  value = google_storage_bucket.orders.name
}

output "topic" {
  value = google_pubsub_topic.orders.id
}

output "subscription" {
  value = google_pubsub_subscription.orders.id
}
