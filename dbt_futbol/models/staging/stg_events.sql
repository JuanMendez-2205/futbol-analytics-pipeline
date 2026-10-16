-- Columnas comunes a todos los eventos. Las específicas de remates y pases
-- se sacan en sus propios modelos (stg_shots, stg_passes).
select
    event_id,
    match_id,
    cast(payload ->> 'index' as integer)            as event_index,
    cast(payload ->> 'period' as integer)           as period,
    cast(payload ->> 'minute' as integer)           as minute,
    cast(payload ->> 'second' as integer)           as second,
    payload -> 'type' ->> 'name'                    as event_type,
    payload -> 'team' ->> 'name'                    as team,
    payload -> 'player' ->> 'name'                  as player,
    payload -> 'position' ->> 'name'                as position,
    cast(payload -> 'location' ->> 0 as double)     as x,
    cast(payload -> 'location' ->> 1 as double)     as y,
    payload
from {{ source('raw', 'events') }}
