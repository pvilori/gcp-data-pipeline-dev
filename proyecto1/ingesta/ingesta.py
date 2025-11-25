import functions_framework
from google.cloud import bigquery
import os

# --- PARAMETRIZACIÓN DEL ENTORNO EMPRESARIAL ---
# Las variables de entorno son inyectadas en el despliegue (CI/CD o gcloud CLI)
DATASET_ID = os.environ.get("DATASET_ID") # Nombre del conjunto de datos en BQ
TABLE_ID = os.environ.get("TABLE_ID")     # Nombre de la tabla de destino en BQ
PROJECT_ID = os.environ.get("GCP_PROJECT") # ID del proyecto donde se ejecuta (Automático)

# Inicializar Cliente: Utiliza automáticamente la Service Account de la CF
bigquery_client = bigquery.Client(project=PROJECT_ID)

@functions_framework.cloud_event
def trigger_bq_load(cloud_event):
    """
    Función activada por un evento de Cloud Storage (finalización de subida).
    Inicia un trabajo de carga asíncrona (Load Job) de GCS a BigQuery.

    Args:
        cloud_event: Objeto CloudEvent con metadatos del archivo.
    """
    if not DATASET_ID or not TABLE_ID:
        # Control de errores y parametrización
        raise ValueError("Variables de entorno DATASET_ID o TABLE_ID no definidas.")
        
    # 1. Extracción de Metadatos y URI
    data = cloud_event.data
    bucket_name = data["bucket"]
    file_name = data["name"]
    file_uri = f"gs://{bucket_name}/{file_name}"
    
    print(f"Evento GCS detectado. URI de origen: {file_uri}")

    # 2. Configuración del Destino y Job de Carga
    table_ref = bigquery_client.dataset(DATASET_ID).table(TABLE_ID)

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1, # Asume que el CSV tiene una fila de cabecera
        autodetect=True,     # Permite a BigQuery inferir el esquema
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND, # Añadir datos
    )

    # 3. Iniciar el Trabajo de Carga Asíncrono (ELT)
    try:
        load_job = bigquery_client.load_table_from_uri(
            file_uri, 
            table_ref, 
            job_config=job_config
        )  
        
        # El trabajo se ejecuta en el backend de BQ; la CF termina rápidamente.
        print(f"Trabajo de BigQuery iniciado. ID: {load_job.job_id}")

    except Exception as e:
        print(f"Error crítico al iniciar el trabajo de carga de BigQuery: {e}")
        # En producción, esto debe alertar vía Pub/Sub o Monitoring.
        raise e