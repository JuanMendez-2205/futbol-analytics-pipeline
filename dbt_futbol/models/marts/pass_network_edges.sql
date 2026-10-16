-- Aristas de la red de pases: cuántos pases completados entre cada par de
-- jugadores en un partido. Es la entrada del grafo de viz/pass_network.py.
select
    match_id,
    team,
    player     as passer,
    recipient,
    count(*)   as passes
from {{ ref('stg_passes') }}
where is_completed and recipient is not null
group by match_id, team, player, recipient
