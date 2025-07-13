{{
  config(
    materialized='view',
    schema='staging'
  )
}}

SELECT
    id AS message_id,
    date AS message_date,
    message,
    views,
    has_media,
    channel AS channel_name,
    image_path,
    scraped_at,
    -- Extract potential product mentions using regex
    REGEXP_MATCHES(message, '(?i)\b(paracetamol|amoxicillin|insulin|vitamin|mask|sanitizer)\b') AS potential_products
FROM {{ source('raw', 'telegram_messages') }}

-- Add test for this model in schema.yml