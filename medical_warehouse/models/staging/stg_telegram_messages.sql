with source as (
    select * from raw_messages
),

cleaned as (
    select
        message_id,
        channel_name,
        message_date::date         as message_date,
        message_date::time         as message_time,
        message_text,
        has_media,
        image_path,
        views,
        forwards,
        scraped_at,
        loaded_at
    from source
    where message_id is not null
)

select * from cleaned