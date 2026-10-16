-- Remates con el contexto del partido: una fila por remate.
-- Se excluye la tanda de penales: no es juego y no cuenta en el resultado.
select
    s.*,
    m.match_date,
    m.stage,
    case when s.team = m.home_team then m.away_team else m.home_team end as opponent
from {{ ref('stg_shots') }} s
join {{ ref('stg_matches') }} m using (match_id)
where not s.is_shootout
