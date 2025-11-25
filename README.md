# gcp-data-pipeline-dev: Plataforma ELT y Orquestación.

Este repositorio contiene la arquitectura de datos ELT (Extract, Load, Transform) desplegada en Google Cloud Platform (GCP), diseñada para la **automatización de la ingesta de datos** y la **orquestación de flujos de trabajo** complejos, incluyendo un patrón seguro para interactuar con APIs externas con límites de tasa (Rate Limiting).

---

## Arquitectura Central

La plataforma se basa en dos flujos principales, ambos gestionados de forma serverless y con Infraestructura como Código (IaC) a través de Terraform:

1.  **Ingesta Serverless:** GCS ➡️ Cloud Function (Gen 2) ➡️ BigQuery (Capa RAW).
2.  **Orquestación de Transformación:** Cloud Composer (Airflow) orquesta las transformaciones SQL en BigQuery.
3.  **Procesamiento de API:** Patrón Pub/Sub + Cloud Run para manejar llamadas al Call Center con límite estricto de 10 RPS.


---

## Requisitos e Inicio Rápido

Para desplegar y trabajar con esta solución, necesitas:

* **Herramientas Locales:** Git, Python 3.11+, Google Cloud CLI (`gcloud`), Terraform (v1.6+).
* **Autenticación:** Credenciales de Aplicación Predeterminadas (ADC) y **Workload Identity Federation (WIF)** configurada en el repositorio para el CI/CD.

### Despliegue con CI/CD

El despliegue de toda la infraestructura y la Cloud Function se realiza automáticamente mediante **GitHub Actions** al hacer *push* a la rama `main`, gracias al pipeline que utiliza Terraform.

```bash
# 1. Configura tus secretos en GitHub (PROD_GCP_PROJECT_ID, WIF_PROVIDER, etc.)
# 2. Revisa y aprueba el plan de Terraform si se requiere intervención manual.

# Para ejecutar el pipeline localmente (Solo Plan):
cd terraform/
terraform init
terraform plan -var "project_id=<TU_PROYECTO>"