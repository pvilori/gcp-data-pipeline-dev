terraform {
  # 1. Requisito de la Versión del Lenguaje Terraform
  required_version = ">= 1.6.0" 

  # 2. Configuración del Backend (Almacenamiento del Estado)
  # Usaremos Google Cloud Storage (GCS) para guardar el archivo de estado de Terraform (.tfstate).
  # Esto es fundamental en entornos de equipo y CI/CD.
  backend "gcs" {
    # Estos valores se inyectan en el CI/CD, pero deben estar presentes aquí.
    bucket = "terraform-state-bucket-empresa"  
    prefix = "prd/cf_ingesta" 
  }

  # 3. Requisito y Configuración de los Proveedores (Plugins)
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"  # Especifica la versión mínima compatible
    }
  }
}

# 4. Configuración del Proveedor
# Define explícitamente el proyecto y la región con variables para el proveedor Google
provider "google" {
  project = var.project_id # Hace referencia a la variable definida en variables.tf
  region  = var.region     # Hace referencia a la variable definida en variables.tf
}