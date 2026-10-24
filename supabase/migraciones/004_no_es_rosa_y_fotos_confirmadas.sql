-- 004: "No es una rosa" en las dudosas y fotos confirmadas para practicar.
--
-- 1. Un experto puede responder que la foto no es una rosa (el robot fotografió una hoja, una mano, un
--    poste…). Queda en etiquetas_expertos con categoria = 'no_rosa': también le sirve a RosaNet y al
--    detector como ejemplo negativo.
-- 2. fotos_confirmadas(): fotos reales del robot con su categoría confirmada, para que el juego y
--    "Aprender" no repitan siempre las mismas fotos de la finca:
--    - las dudosas que clasificó un experto (menos las "no es una rosa");
--    - las rosas que el robot mandó a cortar muy seguro (óptimas con confianza >= 0,8) y que nadie
--      corrigió. Las "lista mañana" no entran: no está claro en qué categoría del juego caen.

alter table etiquetas_expertos drop constraint if exists etiquetas_expertos_categoria_check;
alter table etiquetas_expertos add constraint etiquetas_expertos_categoria_check
  check (categoria in ('1_inmaduro', '2_optimo', '3_pasado', 'no_rosa'));

create or replace function fotos_confirmadas()
returns table (id text, categoria text, foto text, fuente text, fecha timestamptz)
language sql stable security definer set search_path = public as $$
  with expertos as (
    select e.id_ronda || '/' || e.rosa_id as id, e.categoria, d->>'foto' as foto, 'experto'::text as fuente, e.fecha
    from etiquetas_expertos e
    join reportes r on r.id_ronda = e.id_ronda
    cross join lateral jsonb_array_elements(coalesce(r.datos->'dudosas', '[]'::jsonb)) d
    where d->>'rosa_id' = e.rosa_id
      and e.categoria <> 'no_rosa'
      and d->>'foto' like 'http%'
  ),
  robot as (
    select r.id_ronda || '/' || (l->>'rosa_id') as id,
           '2_optimo'::text as categoria,
           l->>'foto' as foto, 'robot'::text as fuente, r.recibido as fecha
    from reportes r
    cross join lateral jsonb_array_elements(coalesce(r.datos->'rosas_listas', '[]'::jsonb)) l
    where l->>'foto' like 'http%'
      and l->>'estado' = 'optimo'
      and (l->>'confianza')::numeric >= 0.8
      and not exists (
        select 1 from etiquetas_expertos e where e.id_ronda = r.id_ronda and e.rosa_id = l->>'rosa_id'
      )
  )
  select * from (select * from expertos union all select * from robot) t
  order by fecha desc
  limit 300;
$$;

grant execute on function fotos_confirmadas() to anon, authenticated;
