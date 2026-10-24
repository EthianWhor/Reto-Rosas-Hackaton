-- 002: roles de coordinación, experto y en capacitación + revisión de rosas dudosas (2026-10-24).
-- Se corre una sola vez sobre una base con la migración 001. No borra datos.
--
-- - Los "trabajador" pasan a "aprendiz" (en capacitación); la coordinación los promueve a "experto".
-- - Los expertos revisan las rosas en las que el robot dudó; sus respuestas quedan en
--   etiquetas_expertos para reentrenar a RosaNet.

-- Roles
alter table personas drop constraint if exists personas_rol_check;
update personas set rol = 'aprendiz' where rol = 'trabajador';
alter table personas add constraint personas_rol_check check (rol in ('admin', 'experto', 'aprendiz'));

create or replace function crear_persona(p_token uuid, p_nombre text, p_rol text, p_pin text)
returns text language plpgsql security definer set search_path = public, extensions as $$
declare
  nuevo text;
begin
  perform _persona_de(p_token, true);
  if p_pin !~ '^\d{4}$' then
    raise exception 'El PIN debe tener 4 números.';
  end if;
  if p_rol not in ('admin', 'experto', 'aprendiz') then
    raise exception 'Rol no válido.';
  end if;
  insert into personas (nombre, rol, pin_hash) values (trim(p_nombre), p_rol, crypt(p_pin, gen_salt('bf')))
  returning id into nuevo;
  return nuevo;
end $$;

-- Cambia el rol de alguien (por ejemplo, promover de "aprendiz" a "experto"). Solo coordinación.
create or replace function cambiar_rol(p_token uuid, p_persona text, p_rol text)
returns void language plpgsql security definer set search_path = public, extensions as $$
declare
  yo personas := _persona_de(p_token, true);
begin
  if p_rol not in ('admin', 'experto', 'aprendiz') then
    raise exception 'Rol no válido.';
  end if;
  if p_persona = yo.id then
    raise exception 'No puedes cambiar tu propio rol.';
  end if;
  update personas set rol = p_rol where id = p_persona and activo;
end $$;

-- Rosas dudosas revisadas por expertos (verdad de terreno para reentrenar a RosaNet)
create table if not exists etiquetas_expertos (
  id bigint generated always as identity primary key,
  id_ronda text not null,
  rosa_id text not null,
  cuadrante_id text,
  categoria text not null check (categoria in ('1_inmaduro', '2_optimo', '3_pasado')),
  persona_id text not null references personas (id) on delete cascade,
  fecha timestamptz not null default now(),
  unique (id_ronda, rosa_id)
);
alter table etiquetas_expertos enable row level security;
-- Sin políticas: la app escribe y consulta con las funciones; el equipo del modelo lee con service_role.

create or replace function etiquetar_dudosa(p_token uuid, p_id_ronda text, p_rosa_id text, p_cuadrante text, p_categoria text)
returns void language plpgsql security definer set search_path = public, extensions as $$
declare
  p personas := _persona_de(p_token);
begin
  if p.rol not in ('experto', 'admin') then
    raise exception 'Solo los expertos pueden revisar dudosas.';
  end if;
  insert into etiquetas_expertos (id_ronda, rosa_id, cuadrante_id, categoria, persona_id)
  values (p_id_ronda, p_rosa_id, p_cuadrante, p_categoria, p.id)
  on conflict (id_ronda, rosa_id) do update
    set categoria = excluded.categoria, persona_id = excluded.persona_id, fecha = now();
end $$;

-- Qué dudosas de una ronda ya se revisaron (solo los ids, sin datos de personas).
create or replace function dudosas_revisadas(p_id_ronda text)
returns setof text language sql security definer set search_path = public as $$
  select rosa_id from etiquetas_expertos where id_ronda = p_id_ronda;
$$;

grant execute on function cambiar_rol(uuid, text, text), etiquetar_dudosa(uuid, text, text, text, text),
  dudosas_revisadas(text) to anon, authenticated;
