-- Test de reconciliación: goles de remates + goles en contra tienen que dar
-- EXACTAMENTE el resultado oficial de cada partido (sin tanda de penales).
-- Este test detectó un bug real: al principio se sumaban los penales de la tanda.
with shot_goals as (
    select match_id, sum(case when is_goal then 1 else 0 end) as goals
    from {{ ref('stg_shots') }}
    where not is_shootout
    group by match_id
),
own_goals as (
    select match_id, count(*) as goals
    from {{ ref('stg_events') }}
    where event_type = 'Own Goal Against'
    group by match_id
)
select
    m.match_id,
    m.home_score + m.away_score                          as official_goals,
    coalesce(s.goals, 0) + coalesce(o.goals, 0)          as event_goals
from {{ ref('stg_matches') }} m
left join shot_goals s using (match_id)
left join own_goals  o using (match_id)
where m.home_score + m.away_score <> coalesce(s.goals, 0) + coalesce(o.goals, 0)
