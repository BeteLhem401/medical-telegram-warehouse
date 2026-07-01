with detections as (
    select * from raw_yolo_detections
),

messages as (
    select * from {{ ref('fct_messages') }}
)

select
    d.message_id,
    m.channel_key,
    m.date_key,
    d.detected_class,
    d.confidence_score,
    d.image_category
from detections d
left join messages m on d.message_id = m.message_id