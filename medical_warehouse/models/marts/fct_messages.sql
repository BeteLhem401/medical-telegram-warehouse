with messages as (
    select * from {{ ref('stg_telegram_messages') }}
)

select
    message_id,
    channel_name,
    message_date,
    message_time,
    message_text,
    has_media,
    image_path,
    views,
    forwards,
    scraped_at
from messages
