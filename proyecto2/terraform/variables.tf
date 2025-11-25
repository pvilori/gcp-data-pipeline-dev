variable "project_id" {
  description = "ID del proyecto GCP objetivo."
  type        = string
}

variable "region" {
  description = "Región de GCP para el despliegue."
  type        = string
  default     = "us-central1"
}

variable "env_name" {
  description = "Nombre del entorno (ej: dev, prod). Se usa para nombrar recursos."
  type        = string
}

variable "cf_runtime_sa_email" {
  description = "Email de la Service Account que ejecutará la Cloud Function (Mínimo Privilegio)."
  type        = string
}

variable "bq_dataset_id" {
  description = "ID del BigQuery Dataset de destino (variable de entorno para la CF)."
  type        = string
}