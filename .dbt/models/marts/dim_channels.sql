{{
  config(
    materialized='table',
    schema='analytics'
  )
}}

WITH channel_stats AS (
    SELECT
        channel_name,
        COUNT(*) AS total_messages,
        COUNT(CASE WHEN has_media THEN 1 END) AS media_messages,
        MIN(message_date) AS first_seen,
        MAX(message_date) AS last_seen
    FROM {{ ref('stg_telegram_messages') }}
    GROUP BY 1
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['channel_name']) }} AS channel_key,
    channel_name,
    total_messages,
    media_messages,
    ROUND(media_messages * 100.0 / NULLIF(total_messages, 0), 2) AS media_percentage,
    first_seen,
    last_seen,
    {{ dbt_utils.current_timestamp() }} AS dbt_processed_at
FROM channel_stats