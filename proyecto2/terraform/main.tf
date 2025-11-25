# 1. Bucket para almacenar el código fuente empaquetado (.zip)
resource "google_storage_bucket" "source_bucket" {
  project      = var.project_id
  name         = "tf-source-cf-${var.env_name}-${var.project_id}"
  location     = var.region
  uniform_bucket_level_access = true
  force_destroy = true
}

# 2. Bucket de Ingesta (Trigger Resource)
resource "google_storage_bucket" "ingest_bucket" {
  project      = var.project_id
  name         = "data-ingesta-${var.env_name}-${var.project_id}"
  location     = var.region
  uniform_bucket_level_access = true
}

# 3. Cloud Function (Gen 2 - Basada en Cloud Run)
resource "google_cloud_run_v2_service" "cf_ingesta" {
  project  = var.project_id
  name     = "cf-ingesta-gcs-bq-${var.env_name}"
  location = var.region

  template {
    service_account = var.cf_runtime_sa_email
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello" # Placeholder; la fuente se actualiza con el despliegue del código
    }
  }

  # Configuración del Eventarc Trigger (Enlace GCS)
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Se crea un 'trigger' de Eventarc para enlazar la Cloud Function al Bucket de Ingesta
resource "google_eventarc_trigger" "gcs_trigger" {
  project  = var.project_id
  name     = "trigger-ingesta-${var.env_name}"
  location = var.region # Debe coincidir con la región de la CF

  matching_criteria {
    attribute = "type"
    value     = "google.cloud.storage.object.v1.finalized"
  }
  matching_criteria {
    attribute = "bucket"
    value     = google_storage_bucket.ingest_bucket.name
  }

  destination {
    cloud_run_service {
      service = google_cloud_run_v2_service.cf_ingesta.name
      region  = var.region
    }
  }

  service_account = var.cf_runtime_sa_email
}