-- Resumen por equipo y partido: remates, xG, pases y precisión.
with shots as (
    select match_id, team,
           count(*)                                 as shots,
           sum(case when is_goal then 1 else 0 end) as goals,
           sum(xg)                                  as xg
    from {{ ref('stg_shots') }}
    where not is_shootout
    group by match_id, team
),
passes as (
    select match_id, team,
           count(*)                                         as passes,
           sum(case when is_completed then 1 else 0 end)    as passes_completed
    from {{ ref('stg_passes') }}
    group by match_id, team
)
select
    p.match_id,
    m.match_date,
    m.stage,
    p.team,
    coalesce(s.shots, 0)                              as shots,
    coalesce(s.goals, 0)                              as goals,
    round(coalesce(s.xg, 0), 2)                       as xg,
    p.passes,
    p.passes_completed,
    round(100.0 * p.passes_completed / p.passes, 1)   as pass_accuracy_pct
from passes p
left join shots s using (match_id, team)
join {{ ref('stg_matches') }} m on m.match_id = p.match_id
