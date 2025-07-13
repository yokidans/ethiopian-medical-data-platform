{{
  config(
    materialized='table',
    schema='analytics'
  )
}}

WITH date_series AS (
    SELECT 
        generate_series(
            (SELECT MIN(DATE(message_date)) FROM {{ ref('stg_telegram_messages') }}),
            (SELECT MAX(DATE(message_date)) FROM {{ ref('stg_telegram_messages') }}),
            interval '1 day'
        )::DATE AS date
)

SELECT
    date,
    EXTRACT(YEAR FROM date) AS year,
    EXTRACT(QUARTER FROM date) AS quarter,
    EXTRACT(MONTH FROM date) AS month,
    EXTRACT(DAY FROM date) AS day,
    EXTRACT(DOW FROM date) AS day_of_week,
    TO_CHAR(date, 'Day') AS day_name,
    CASE WHEN EXTRACT(DOW FROM date) IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend
FROM date_series