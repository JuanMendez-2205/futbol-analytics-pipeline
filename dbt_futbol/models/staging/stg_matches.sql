-- Un partido por fila, con los campos del JSON ya tipados.
select
    match_id,
    competition_id,
    season_id,
    cast(payload ->> 'match_date' as date)                         as match_date,
    payload -> 'competition_stage' ->> 'name'                      as stage,
    payload -> 'home_team' ->> 'home_team_name'                    as home_team,
    payload -> 'away_team' ->> 'away_team_name'                    as away_team,
    cast(payload ->> 'home_score' as integer)                      as home_score,
    cast(payload ->> 'away_score' as integer)                      as away_score
from {{ source('raw', 'matches') }}
