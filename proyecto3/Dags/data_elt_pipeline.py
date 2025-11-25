from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
# Operadores nativos de Google
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.models.baseoperator import chain
from airflow.models.variable import Variable # Importación para parametrización

# --------------------------------------------------------------------------------
# 1. PARAMETRIZACIÓN DEL ENTORNO EMPRESARIAL (AIRFLOW VARIABLES)
# --------------------------------------------------------------------------------

# Se lee la configuración desde las Variables de Airflow (UI de Composer o CLI)
# Los valores por defecto se usan en entornos de desarrollo local si no se definen.
PROJECT_ID = Variable.get("gcp_project_id", default="gcp-data-project-dev")
GCS_BUCKET_LANDING = Variable.get("gcs_bucket_landing", default="landing-zone-data-in")
GCS_SQL_FOLDER = Variable.get("gcs_sql_folder", default="dags/sql")

BQ_RAW_DATASET = Variable.get("bq_raw_dataset", default="01_raw_data")
BQ_RAW_TABLE = Variable.get("bq_raw_table", default="transactions_inbound")

BQ_FINAL_DATASET = Variable.get("bq_final_dataset", default="02_data_mart")
BQ_FINAL_TABLE = Variable.get("bq_final_table", default="transactions_clean")

# La Service Account de ejecución es la SA del Worker de Airflow
COMPOSER_SA = f"serviceAccount:{PROJECT_ID}-composer-sa@gcp-sa-composer.iam.gserviceaccount.com" 

# --------------------------------------------------------------------------------
# 2. DEFINICIÓN DEL DAG
# --------------------------------------------------------------------------------

with DAG(
    dag_id="elt_gcs_bq_transformation_pipeline",
    start_date=pendulum.datetime(2023, 1, 1, tz="UTC"),
    schedule=None, # Ejecución manual o disparada
    catchup=False,
    tags=["gcp", "elt", "bigquery"],
    doc_md="""
    ## ETL Pipeline Empresarial

    Este DAG implementa un flujo ELT desacoplado y utiliza operadores nativos de GCP.
    El flujo consiste en:
    1. Cargar un archivo CSV desde GCS a BigQuery (RAW layer).
    2. Ejecutar una transformación SQL compleja y guardarla en una nueva tabla (MART layer).

    **Parametrización:** Todos los nombres de recursos son gestionados mediante Airflow Variables.
    """
) as dag:
    # --------------------------------------------------------------------
    # Tarea 1: LOAD (Cargar Archivo de GCS a BigQuery)
    # --------------------------------------------------------------------
    load_gcs_to_bq = GCSToBigQueryOperator(
        task_id="load_data_from_gcs",
        bucket=GCS_BUCKET_LANDING,
        source_objects=["{{ dag_run.conf.get('file_name', 'default_data/transactions_2024.csv') }}"],
        destination_project_dataset_table=f"{BQ_RAW_DATASET}.{BQ_RAW_TABLE}",
        source_format="CSV",
        skip_leading_rows=1, # Ignora la cabecera
        create_disposition="CREATE_IF_NEEDED",
        write_disposition="WRITE_TRUNCATE", # Sobrescribe la tabla RAW en cada ejecución
        autodetect=True, # Detección automática del esquema
        gcp_conn_id="google_cloud_default", # Conexión estándar de Composer
    )

    # --------------------------------------------------------------------
    # Tarea 2: TRANSFORM (Ejecutar Query de Transformación SQL)
    # --------------------------------------------------------------------
    transform_and_save = BigQueryInsertJobOperator(
        task_id="transform_and_save_to_mart",
        # El JOB de BQ se define en un archivo externo alojado en GCS
        configuration={
            "query": {
                "query": "{% include 'transform_data.sql' %}", # Carga el SQL
                "useLegacySql": False,
                "destinationTable": {
                    "projectId": PROJECT_ID,
                    "datasetId": BQ_FINAL_DATASET,
                    "tableId": BQ_FINAL_TABLE,
                },
                "writeDisposition": "WRITE_TRUNCATE", # Sobrescribe la tabla de destino final
            }
        },
        # Pasar parámetros de Python al SQL
        params={
            "project_id": PROJECT_ID,
            "bq_raw_dataset": BQ_RAW_DATASET,
            "bq_raw_table": BQ_RAW_TABLE,
        },
        gcp_conn_id="google_cloud_default",
        # Le dice al operador dónde encontrar el archivo SQL
        template_searchpath=f"gs://{{{{dag_run.conf.get('composer_gcs_bucket')}}}}/{GCS_SQL_FOLDER}", 
    )

    # --------------------------------------------------------------------
    # 3. DEFINICIÓN DEL FLUJO
    # --------------------------------------------------------------------
    # Tarea 1 >> Tarea 2
    chain(load_gcs_to_bq, transform_and_save)