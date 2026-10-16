-- Definición por jugador en el torneo: goles vs. xG.
-- goals_minus_xg > 0 => convirtió más de lo "esperado" por la calidad de sus remates.
-- Se excluyen penales para no inflar el xG (un penal vale ~0.78 xG).
select
    player,
    team,
    count(*)                                   as shots,
    sum(case when is_goal then 1 else 0 end)   as goals,
    round(sum(xg), 2)                          as xg,
    round(sum(case when is_goal then 1 else 0 end) - sum(xg), 2) as goals_minus_xg,
    round(sum(xg) / count(*), 3)               as xg_per_shot
from {{ ref('fct_shots') }}
where shot_type <> 'Penalty'
group by player, team
