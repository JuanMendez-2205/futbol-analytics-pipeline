select
    event_id,
    match_id,
    period,
    minute,
    team,
    player,
    x,
    y,
    cast(payload -> 'shot' ->> 'statsbomb_xg' as double)   as xg,
    payload -> 'shot' -> 'outcome' ->> 'name'              as outcome,
    payload -> 'shot' -> 'body_part' ->> 'name'            as body_part,
    payload -> 'shot' -> 'type' ->> 'name'                 as shot_type,
    (payload -> 'shot' -> 'outcome' ->> 'name') = 'Goal'   as is_goal,
    period = 5                                             as is_shootout  -- tanda de penales
from {{ ref('stg_events') }}
where event_type = 'Shot'
