-- Test singular: el xG es una probabilidad, tiene que estar entre 0 y 1.
select *
from {{ ref('stg_shots') }}
where xg < 0 or xg > 1
