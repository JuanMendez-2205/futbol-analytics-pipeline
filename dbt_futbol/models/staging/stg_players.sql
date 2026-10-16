-- Dimensión de jugadores: nombre completo (el que usan los eventos) + apodo.
-- Los eventos dicen "Lionel Andrés Messi Cuccittini"; el apodo es "Lionel Messi".
with players as (
    select
        l.team,
        p.value ->> 'player_name'                  as player,
        p.value ->> 'player_nickname'              as nickname,
        cast(p.value ->> 'jersey_number' as int)   as jersey_number
    from {{ source('raw', 'lineups') }} l,
         json_each(l.payload -> 'lineup') p
)
select distinct
    team,
    player,
    coalesce(nickname, player) as display_name,
    jersey_number
from players
