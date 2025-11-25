***

## Contenido del Archivo: `ARCHITECTURE.md`

Este archivo contiene la justificación técnica de los componentes de GCP, la seguridad y la parametrización para el entorno empresarial.

```markdown
# Diseño Arquitectónico de la Plataforma de Datos en GCP

Este documento detalla la arquitectura de la plataforma de datos, enfocada en la escalabilidad, el desacoplamiento y el cumplimiento del principio de mínimo privilegio.

---

## 1. Arquitectura de Ingesta y Orquestación (ELT)

### A. Capa Serverless (Ingesta de Archivos)

| Componente | Patrón | Justificación Técnica |
| :--- | :--- | :--- |
| **GCS** | Origen de Evento | Punto de entrada desacoplado. El evento `finalize` dispara el flujo. |
| **Cloud Function Gen 2** | Event-Driven | Mínima latencia, ideal para tareas ligeras. Usa Eventarc implícitamente como bus de eventos. |
| **BigQuery (RAW Layer)** | Destino ELT | Se utiliza el método nativo `load_table_from_uri` para **Carga Directa**, evitando el procesamiento en memoria de la CF. Es el patrón más eficiente y económico para archivos grandes. |

### B. Orquestación y Transformación

La lógica de transformación se aísla en **BigQuery** para aprovechar su potencia de procesamiento MPP (Massively Parallel Processing).

* **Servicio:** **Cloud Composer (Apache Airflow)**.
* **Función:** Los DAGs (ej: `data_elt_pipeline.py`) utilizan operadores nativos (`GCSToBigQueryOperator`, `BigQueryInsertJobOperator`) para coordinar la carga y ejecución de SQL.
* **Buenas Prácticas:** La lógica de transformación (SQL) está separada del código de orquestación (Python), promoviendo la mantenibilidad y la reutilización de código SQL.

---

## 2. Arquitectura de Procesamiento de API con Rate Limiting

El diseño resuelve el conflicto entre la demanda de datos (600 registros/hora, con posibles picos) y la limitación estricta del proveedor externo (máximo 10 RPS).

### Justificación: Desacoplamiento y Control de Tasa

1.  **Cloud Pub/Sub (Buffer):** Actúa como el amortiguador principal. Absorbe cualquier pico en la generación de los 600 registros, convirtiéndolos en mensajes persistentes. Esto asegura que ningún dato se pierda.
2.  **Cloud Scheduler (Marcapasos/Rate Limiter):** Es el componente de control. Se configura para disparar un evento **exactamente 10 veces por segundo** (o a la tasa límite).
3.  **Cloud Run (Procesador):** Un servicio de Cloud Run suscrito al Scheduler. Este servicio lee **un mensaje** de Pub/Sub por cada activación del Scheduler y realiza la llamada a la API externa.
    * **Configuración clave:** El servicio debe limitarse a un máximo de 10 instancias con concurrencia de 1 para garantizar que el límite de 10 RPS no se exceda, respetando el SLA del proveedor.
4.  **DLQ (Dead Letter Queue):** Los mensajes que fallan crónicamente (errores 5xx o reintentos fallidos) son enviados a una cola separada para inspección manual, manteniendo el flujo principal operativo.

---

## 3. Parametrización y CI/CD (Terraform)

La portabilidad del entorno se logra mediante la inyección de variables de configuración.

* **IaC (Terraform):** Toda la infraestructura (Buckets, Cloud Functions, IAM Bindings) se define en `terraform/`.
* **Autenticación Segura:** Se utiliza **Workload Identity Federation (WIF)** para que el pipeline de GitHub Actions se autentique en GCP **sin usar claves de servicio estáticas**.
* **Parametrización:** Los nombres de recursos (`project_id`, `bq_dataset_id`, `cf_runtime_sa_email`) se inyectan en tiempo de ejecución a través de variables de Terraform o Secrets de GitHub, asegurando la separación del código entre entornos Dev/Prod.