with source as (
    select * from {{ ref('stg_telegram_messages') }}
),

channel_stats as (
    select
        channel_name,
        min(message_date) as first_post_date,
        max(message_date) as last_post_date,
        count(*)          as total_posts,
        avg(view_count)   as avg_views
    from source
    group by channel_name
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['channel_name']) }} as channel_key,
        channel_name,
        case
            when channel_name = 'lobelia4cosmetics' then 'Cosmetics'
            when channel_name = 'tikvahpharma'      then 'Pharmaceutical'
            when channel_name = 'CheMed123'         then 'Medical'
            else 'Other'
        end as channel_type,
        first_post_date,
        last_post_date,
        total_posts,
        avg_views
    from channel_stats
)

select * from final