# --------------------------------------------------------------------------------
# LÓGICA DE TRANSFORMACIÓN DE DATOS (BUSINESS LOGIC)
# Este SQL transforma los datos crudos (RAW) en un formato limpio (MART)
# --------------------------------------------------------------------------------

SELECT
    t1.transaction_id,
    t1.customer_id,
    # Conversión de timestamp a tipo DATE y extracción del año para particionamiento
    DATE(t1.transaction_timestamp) AS transaction_date,
    EXTRACT(YEAR FROM t1.transaction_timestamp) AS transaction_year,
    t1.amount,
    # Creación de una columna de clasificación simple
    CASE
        WHEN t1.amount >= 500 THEN 'HIGH_VALUE'
        ELSE 'STANDARD'
    END AS value_segment,
    t2.region_name
FROM
    # La tabla cruda (destino del paso de carga del DAG)
    `{{ params.project_id }}.{{ params.bq_raw_dataset }}.{{ params.bq_raw_table }}` AS t1
INNER JOIN
    # Una tabla de referencia (asumida) para enriquecimiento
    `{{ params.project_id }}.reference.customer_regions` AS t2
ON
    t1.customer_id = t2.customer_id
WHERE
    # Filtrado de registros inválidos o de prueba
    t1.is_valid = TRUE