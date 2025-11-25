#!/bin/bash

# --- 1. PARÁMETROS DEL ENTORNO ---
export GCP_REGION="us-central1"
export BUCKET_INGESTA="mi-bucket-data-prod" 
export RUNTIME_SA_EMAIL="sa-cf-ingesta-bq@<PROJECT_ID>.iam.gserviceaccount.com"
export BQ_DATASET="data_raw"
export BQ_TABLE="datos_crudos"
# -----------------------------------

# --- 2. COMANDO DE DESPLIEGUE ---
echo "Iniciando despliegue de Cloud Function..."

gcloud functions deploy trigger-bq-load \
  --gen2 \
  --runtime python311 \
  --entry-point trigger_bq_load \
  --source cloud_functions/cf_ingesta_gcs_bq \
  --region $GCP_REGION \
  --service-account $RUNTIME_SA_EMAIL \
  --trigger-event google.cloud.storage.object.v1.finalized \
  --trigger-resource $BUCKET_INGESTA \
  --set-env-vars DATASET_ID=$BQ_DATASET,TABLE_ID=$BQ_TABLE \
  --timeout 300s \
  --memory 256Mi

echo "Despliegue completado."