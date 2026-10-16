-- Test genérico propio (sin depender del paquete dbt_utils): falla si la combinación
-- de columnas se repite.
{% test unique_combination(model, columns) %}
select {{ columns | join(', ') }}, count(*) as n
from {{ model }}
group by {{ columns | join(', ') }}
having count(*) > 1
{% endtest %}
