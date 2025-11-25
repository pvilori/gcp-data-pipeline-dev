# Validaciones de Negocio y API para la Arquitectura de Llamadas

Antes de finalizar la arquitectura del Call Center, es vital validar los siguientes puntos con las áreas de negocio y el proveedor de la API para garantizar el cumplimiento del SLA y la robustez del sistema.

---

## A. Preguntas a las Áreas de Negocio (Demanda y Timing)

La arquitectura está diseñada para un promedio de 0.167 RPS (600/3600), pero necesitamos entender los picos reales.

1.  **Timing y Latencia Crítica:**
    * ¿Cuál es la **latencia máxima aceptable** (en segundos/minutos) desde que se genera un registro hasta que se debe intentar la llamada a la API? (Esto define la presión en la cola de Pub/Sub).
    * ¿Existen picos estacionales o diarios donde la tasa de generación de 600 registros/hora se supera en un factor de 10x o más?
2.  **Volumen y Patrón de Generación:**
    * La generación de 600 registros/hora, ¿es constante (distribuida uniformemente) o se genera en grandes bloques (ej: al final de un proceso ETL a las 2:00 AM)?
3.  **Manejo de Errores Lógicos:**
    * Si la API rechaza la llamada debido a datos inválidos (ej: número de teléfono mal formado), ¿cuál es la política de negocio? (¿A la DLQ o a un sistema de corrección manual?).
4.  **Priorización:**
    * ¿Hay categorías de clientes o tipos de registros que deban tener una **prioridad más alta** y saltarse la cola de Pub/Sub más rápidamente?

---

## B. Preguntas al Proveedor de la API (Técnico y Confiabilidad)

Es crucial entender cómo el proveedor impone y maneja el límite de 10 RPS.

1.  **Límites de Tasa (Rate Limiting):**
    * El límite es 10 RPS. **¿Este límite es estricto, o la API permite un pequeño margen ("burst capacity") antes de aplicar el rechazo (429)?**
    * ¿Cuál es el código de respuesta HTTP exacto (ej: **429 Too Many Requests**) que se retorna cuando excedemos el límite, y se incluye el encabezado **`Retry-After`**? (Esto permite a nuestro Cloud Run reintentar de forma inteligente).
2.  **Confiabilidad e Idempotencia:**
    * **¿La API es idempotente?** Es decir, si el proceso falla justo después de enviar el request, y nuestro sistema reintenta, ¿el proveedor garantiza que solo se crea **una sola llamada**?
    * ¿Cuál es la latencia promedio de respuesta de la API? (Necesario para calcular el *timeout* del Cloud Run).
3.  **Seguridad:**
    * ¿La autenticación es mediante clave de API en el encabezado o requiere un flujo de tokens OAuth2?