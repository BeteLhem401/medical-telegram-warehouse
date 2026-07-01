with source as (
    select * from raw_messages
),

cleaned as (
    select
        message_id,
        channel_name,
        message_date::date                          as message_date,
        message_date::time                          as message_time,
        message_text,
        coalesce(length(message_text), 0)           as message_length,
        has_media                                   as has_image,
        image_path,
        coalesce(views, 0)                          as view_count,
        coalesce(forwards, 0)                       as forward_count,
        scraped_at,
        loaded_at
    from source
    where message_id is not null
      and channel_name is not null
)

select * from cleaned