-- En StatsBomb un pase completado NO tiene pass.outcome (es null).
select
    event_id,
    match_id,
    minute,
    team,
    player,
    payload -> 'pass' -> 'recipient' ->> 'name'                as recipient,
    x,
    y,
    cast(payload -> 'pass' -> 'end_location' ->> 0 as double)  as end_x,
    cast(payload -> 'pass' -> 'end_location' ->> 1 as double)  as end_y,
    payload -> 'pass' -> 'outcome' ->> 'name'                  as outcome,
    (payload -> 'pass' -> 'outcome') is null                   as is_completed
from {{ ref('stg_events') }}
where event_type = 'Pass'
