select *
from {{ ref('fct_messages') }} f
join {{ ref('dim_dates') }} d on f.date_key = d.date_key
where d.full_date > current_date