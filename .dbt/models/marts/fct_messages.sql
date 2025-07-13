{{
  config(
    materialized='table',
    schema='analytics'
  )
}}

WITH messages AS (
    SELECT
        m.message_id,
        m.message_date,
        m.message,
        m.views,
        m.has_media,
        m.image_path,
        m.channel_name,
        m.potential_products,
        LENGTH(m.message) AS message_length,
        {{ dbt_utils.generate_surrogate_key(['m.channel_name']) }} AS channel_key,
        {{ dbt_utils.generate_surrogate_key(['DATE(m.message_date)']) }} AS date_key
    FROM {{ ref('stg_telegram_messages') }} m
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['message_id']) }} AS message_key,
    message_id,
    message_date,
    channel_key,
    date_key,
    message,
    views,
    has_media,
    image_path,
    message_length,
    potential_products,
    {{ dbt_utils.current_timestamp() }} AS dbt_processed_at
FROM messages