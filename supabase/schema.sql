-- Base de datos de Punto 3 en Supabase (proyecto fxlljandvphujxxddvxy).
-- La comparten la app de la tablet, el robot y, más adelante, las gafas.
-- Se corre completo en el SQL Editor de Supabase. Se puede volver a correr: borra y recrea todo
-- (OJO: también borra los datos).
--
-- Seguridad:
-- - La app usa la clave pública (anon). Con ella solo puede LEER los datos del turno
--   (reportes, configuración, asistencia y cuadrantes hechos), que no son sensibles.
-- - Todo lo que ESCRIBE pasa por funciones que exigen una sesión abierta con nombre + PIN.
--   El PIN se guarda cifrado (bcrypt) y nunca sale de la base.
-- - El robot sube los reportes con la clave service_role, que solo vive en el robot (robot/.env).

create extension if not exists pgcrypto with schema extensions;

drop table if exists etiquetas_expertos, rondas_juego, cuadrantes_hechos, asistencia, config_turno, reportes, sesiones, personas,
  version_personas cascade;

-- ---------------------------------------------------------------- tablas

create table personas (
  id text primary key default 'p-' || substr(md5(random()::text), 1, 10),
  nombre text not null,
  rol text not null check (rol in ('admin', 'experto', 'aprendiz')),
  pin_hash text not null,
  activo boolean not null default true,
  creado timestamptz not null default now()
);

create table sesiones (
  token uuid primary key default gen_random_uuid(),
  persona_id text not null references personas (id) on delete cascade,
  creada timestamptz not null default now(),
  expira timestamptz not null default now() + interval '14 hours'
);

-- Un reporte por ronda del robot: el JSON completo (robot/reporte/archivos.py, rama A).
create table reportes (
  id_ronda text primary key,
  invernadero text not null,
  fecha date not null,
  datos jsonb not null,
  recibido timestamptz not null default now()
);

-- Una sola fila (id = 1) con la configuración del turno.
create table config_turno (
  id int primary key default 1 check (id = 1),
  horas_corte numeric not null default 6,
  segundos_por_rosa int not null default 30,
  minutos_por_cuadrante int not null default 2,
  actualizado timestamptz not null default now()
);

-- Quién vino cada día. Si un día no tiene fila, se asume que vinieron todos.
create table asistencia (
  fecha date primary key,
  presentes text[] not null,
  actualizado timestamptz not null default now()
);

create table cuadrantes_hechos (
  id_ronda text not null,
  cuadrante_id text not null,
  persona_id text not null references personas (id) on delete cascade,
  hecho_en timestamptz not null default now(),
  primary key (id_ronda, cuadrante_id)
);

-- Rondas del juego de clasificación (progreso de cada persona).
create table rondas_juego (
  id bigint generated always as identity primary key,
  persona_id text not null references personas (id) on delete cascade,
  fecha timestamptz not null default now(),
  respuestas jsonb not null
);

-- personas no se puede leer con la clave anon (tiene el PIN cifrado), así que Realtime no avisa sus
-- cambios. Cada cambio en personas sube este contador público, que la app escucha para recargar.
create table version_personas (
  id int primary key default 1 check (id = 1),
  version bigint not null default 0,
  actualizado timestamptz not null default now()
);

insert into config_turno (id) values (1);
insert into version_personas (id) values (1);

-- Usuarios de prueba (los mismos de app-tablet/src/data/usuarios.ts). Cambiar los PIN en la finca.
insert into personas (id, nombre, rol, pin_hash) values
  ('admin-1', 'Coordinadora', 'admin',      extensions.crypt('1234', extensions.gen_salt('bf'))),
  ('t-01',    'Marta',        'aprendiz',   extensions.crypt('1001', extensions.gen_salt('bf'))),
  ('t-02',    'Luis',         'aprendiz',   extensions.crypt('1002', extensions.gen_salt('bf'))),
  ('t-03',    'Ana',          'aprendiz',   extensions.crypt('1003', extensions.gen_salt('bf'))),
  ('t-04',    'Carlos',       'aprendiz',   extensions.crypt('1004', extensions.gen_salt('bf'))),
  ('t-05',    'Diana',        'aprendiz',   extensions.crypt('1005', extensions.gen_salt('bf'))),
  ('t-06',    'Jorge',        'aprendiz',   extensions.crypt('1006', extensions.gen_salt('bf'))),
  ('t-07',    'Paola',        'aprendiz',   extensions.crypt('1007', extensions.gen_salt('bf'))),
  ('t-08',    'Andrés',       'aprendiz',   extensions.crypt('1008', extensions.gen_salt('bf'))),
  ('t-09',    'Sandra',       'aprendiz',   extensions.crypt('1009', extensions.gen_salt('bf'))),
  ('t-10',    'Wilson',       'aprendiz',   extensions.crypt('1010', extensions.gen_salt('bf')));

-- ---------------------------------------------------------------- permisos (RLS)

alter table personas enable row level security;
alter table sesiones enable row level security;
alter table reportes enable row level security;
alter table config_turno enable row level security;
alter table asistencia enable row level security;
alter table cuadrantes_hechos enable row level security;
alter table rondas_juego enable row level security;
alter table version_personas enable row level security;

-- Lectura pública de los datos del turno. Sin políticas de escritura: se escribe con las funciones.
create policy lectura on reportes for select to anon, authenticated using (true);
create policy lectura on config_turno for select to anon, authenticated using (true);
create policy lectura on asistencia for select to anon, authenticated using (true);
create policy lectura on cuadrantes_hechos for select to anon, authenticated using (true);
create policy lectura on version_personas for select to anon, authenticated using (true);
-- personas, sesiones y rondas_juego: sin políticas → la clave anon no las ve.

-- Cambios en vivo (la pantalla de la coordinadora se actualiza sola).
alter publication supabase_realtime add table cuadrantes_hechos, asistencia, config_turno, reportes, version_personas;

-- ---------------------------------------------------------------- funciones

-- Persona dueña de una sesión vigente (o error).
create or replace function _persona_de(p_token uuid, p_solo_admin boolean default false)
returns personas language plpgsql security definer set search_path = public, extensions as $$
declare
  p personas;
begin
  select personas.* into p
  from sesiones join personas on personas.id = sesiones.persona_id
  where sesiones.token = p_token and sesiones.expira > now() and personas.activo;
  if not found then
    raise exception 'Sesión vencida. Vuelve a entrar.' using errcode = '28000';
  end if;
  if p_solo_admin and p.rol <> 'admin' then
    raise exception 'Solo la administración puede hacer esto.' using errcode = '42501';
  end if;
  return p;
end $$;

-- Lista para la pantalla de ingreso (sin el PIN).
create or replace function listar_personas()
returns table (id text, nombre text, rol text)
language sql security definer set search_path = public as $$
  select id, nombre, rol from personas where activo order by rol, creado, nombre;
$$;

-- Abre una sesión si el PIN coincide. Devuelve el token, o null si el PIN no coincide.
create or replace function entrar(p_persona text, p_pin text)
returns uuid language plpgsql security definer set search_path = public, extensions as $$
declare
  t uuid;
begin
  if not exists (
    select 1 from personas where id = p_persona and activo and pin_hash = crypt(p_pin, pin_hash)
  ) then
    return null;
  end if;
  delete from sesiones where expira < now();
  insert into sesiones (persona_id) values (p_persona) returning token into t;
  return t;
end $$;

create or replace function salir(p_token uuid)
returns void language sql security definer set search_path = public as $$
  delete from sesiones where token = p_token;
$$;

create or replace function marcar_hecho(p_token uuid, p_id_ronda text, p_cuadrante text, p_hecho boolean)
returns void language plpgsql security definer set search_path = public, extensions as $$
declare
  p personas := _persona_de(p_token);
begin
  if p_hecho then
    insert into cuadrantes_hechos (id_ronda, cuadrante_id, persona_id)
    values (p_id_ronda, p_cuadrante, p.id)
    on conflict (id_ronda, cuadrante_id) do update set persona_id = excluded.persona_id, hecho_en = now();
  else
    delete from cuadrantes_hechos where id_ronda = p_id_ronda and cuadrante_id = p_cuadrante;
  end if;
end $$;

create or replace function guardar_asistencia(p_token uuid, p_fecha date, p_presentes text[])
returns void language plpgsql security definer set search_path = public, extensions as $$
begin
  perform _persona_de(p_token, true);
  insert into asistencia (fecha, presentes) values (p_fecha, p_presentes)
  on conflict (fecha) do update set presentes = excluded.presentes, actualizado = now();
end $$;

create or replace function guardar_config(p_token uuid, p_horas numeric, p_segundos int, p_minutos int)
returns void language plpgsql security definer set search_path = public, extensions as $$
begin
  perform _persona_de(p_token, true);
  update config_turno
  set horas_corte = p_horas, segundos_por_rosa = p_segundos, minutos_por_cuadrante = p_minutos, actualizado = now()
  where id = 1;
end $$;

create or replace function crear_persona(p_token uuid, p_nombre text, p_rol text, p_pin text)
returns text language plpgsql security definer set search_path = public, extensions as $$
declare
  nuevo text;
begin
  perform _persona_de(p_token, true);
  if p_pin !~ '^\d{4}$' then
    raise exception 'El PIN debe tener 4 números.';
  end if;
  insert into personas (nombre, rol, pin_hash) values (trim(p_nombre), p_rol, crypt(p_pin, gen_salt('bf')))
  returning id into nuevo;
  return nuevo;
end $$;

-- No borra: desactiva, para no perder lo que la persona marcó o practicó.
create or replace function quitar_persona(p_token uuid, p_persona text)
returns void language plpgsql security definer set search_path = public, extensions as $$
declare
  yo personas := _persona_de(p_token, true);
begin
  if p_persona = yo.id then
    raise exception 'No te puedes quitar a ti misma.';
  end if;
  update personas set activo = false where id = p_persona;
  delete from sesiones where persona_id = p_persona;
end $$;

create or replace function guardar_ronda_juego(p_token uuid, p_respuestas jsonb)
returns void language plpgsql security definer set search_path = public, extensions as $$
declare
  p personas := _persona_de(p_token);
begin
  insert into rondas_juego (persona_id, respuestas) values (p.id, p_respuestas);
end $$;

create or replace function mis_rondas_juego(p_token uuid)
returns table (fecha timestamptz, respuestas jsonb)
language plpgsql security definer set search_path = public, extensions as $$
declare
  p personas := _persona_de(p_token);
begin
  return query select r.fecha, r.respuestas from rondas_juego r where r.persona_id = p.id order by r.fecha;
end $$;

create or replace function _tocar_personas()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  update version_personas set version = version + 1, actualizado = now() where id = 1;
  return null;
end $$;

create trigger personas_cambian after insert or update or delete on personas
  for each statement execute function _tocar_personas();

-- Las funciones internas no se exponen; las demás sí, para la clave anon.
revoke execute on function _persona_de(uuid, boolean) from public, anon, authenticated;
revoke execute on function _tocar_personas() from public, anon, authenticated;
grant execute on function listar_personas(), entrar(text, text), salir(uuid), marcar_hecho(uuid, text, text, boolean),
  guardar_asistencia(uuid, date, text[]), guardar_config(uuid, numeric, int, int), crear_persona(uuid, text, text, text),
  quitar_persona(uuid, text), guardar_ronda_juego(uuid, jsonb), mis_rondas_juego(uuid)
  to anon, authenticated;

-- ---------------------------------------------------------------- roles y dudosas (migración 002)

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

-- ---------------------------------------------------------------- activación con código (migración 003)

alter table personas alter column pin_hash drop not null;
alter table personas add column if not exists correo text;
alter table personas add column if not exists telefono text;
alter table personas add column if not exists codigo_hash text;
alter table personas add column if not exists codigo_intentos int not null default 0;

-- Validaciones compartidas
create or replace function _validar_datos(p_nombre text, p_correo text, p_telefono text)
returns void language plpgsql immutable as $$
begin
  if trim(coalesce(p_nombre, '')) !~ '^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ''. -]{1,59}$' then
    raise exception 'El nombre solo puede tener letras (mínimo 2).';
  end if;
  if coalesce(p_correo, '') <> '' and p_correo !~* '^[^@\s]+@[^@\s]+\.[a-z]{2,}$' then
    raise exception 'El correo no es válido.';
  end if;
  if coalesce(p_telefono, '') <> '' and regexp_replace(p_telefono, '[\s+()-]', '', 'g') !~ '^\d{7,15}$' then
    raise exception 'El teléfono debe tener entre 7 y 15 números.';
  end if;
end $$;

create or replace function _pin_seguro(p_pin text)
returns boolean language sql immutable as $$
  select p_pin ~ '^\d{4}$'
     and p_pin !~ '^(\d)\1{3}$'
     and p_pin not in ('0123', '1234', '2345', '3456', '4567', '5678', '6789', '9876', '8765', '7654', '6543', '5432', '4321', '3210');
$$;

create or replace function _codigo_nuevo()
returns text language sql volatile as $$
  select lpad((floor(random() * 1000000))::int::text, 6, '0');
$$;

-- Solo personas activadas (con PIN) aparecen para entrar.
create or replace function listar_personas()
returns table (id text, nombre text, rol text)
language sql security definer set search_path = public as $$
  select id, nombre, rol from personas where activo and pin_hash is not null order by rol, creado, nombre;
$$;

-- Para la pantalla "Activar mi usuario": solo nombres, sin datos de contacto.
create or replace function listar_pendientes()
returns table (id text, nombre text)
language sql security definer set search_path = public as $$
  select id, nombre from personas where activo and pin_hash is null and codigo_hash is not null order by nombre;
$$;

-- Lista completa para la coordinación (incluye pendientes y contacto).
create or replace function listar_usuarios(p_token uuid)
returns table (id text, nombre text, rol text, correo text, telefono text, pendiente boolean, bloqueado boolean)
language plpgsql security definer set search_path = public, extensions as $$
begin
  perform _persona_de(p_token, true);
  return query
    select p.id, p.nombre, p.rol, p.correo, p.telefono, p.pin_hash is null, p.codigo_intentos >= 5
    from personas p where p.activo order by p.rol, p.creado, p.nombre;
end $$;

-- Alta: devuelve el id y el código de activación (se muestra una sola vez).
drop function if exists crear_persona(uuid, text, text, text);
create or replace function crear_persona(p_token uuid, p_nombre text, p_correo text, p_telefono text, p_rol text)
returns table (id text, codigo text)
language plpgsql security definer set search_path = public, extensions as $$
declare
  c text := _codigo_nuevo();
  nuevo text;
begin
  perform _persona_de(p_token, true);
  perform _validar_datos(p_nombre, p_correo, p_telefono);
  if p_rol not in ('admin', 'experto', 'aprendiz') then
    raise exception 'Rol no válido.';
  end if;
  insert into personas (nombre, correo, telefono, rol, codigo_hash)
  values (trim(p_nombre), nullif(trim(p_correo), ''), nullif(trim(p_telefono), ''), p_rol, crypt(c, gen_salt('bf')))
  returning personas.id into nuevo;
  return query select nuevo, c;
end $$;

-- Borra el PIN y da un código nuevo (olvidó el PIN, se bloqueó o nunca lo activó).
create or replace function reiniciar_acceso(p_token uuid, p_persona text)
returns text language plpgsql security definer set search_path = public, extensions as $$
declare
  yo personas := _persona_de(p_token, true);
  c text := _codigo_nuevo();
begin
  if p_persona = yo.id then
    raise exception 'No puedes reiniciar tu propio acceso.';
  end if;
  update personas set pin_hash = null, codigo_hash = crypt(c, gen_salt('bf')), codigo_intentos = 0
  where id = p_persona and activo;
  delete from sesiones where persona_id = p_persona;
  return c;
end $$;

-- Revisa el código. Devuelve {ok} o {error}. No usa excepciones para el código incorrecto: una
-- excepción desharía el conteo de intentos.
create or replace function _revisar_codigo(p_persona text, p_codigo text)
returns json language plpgsql security definer set search_path = public, extensions as $$
declare
  p personas;
begin
  select * into p from personas where id = p_persona and activo and pin_hash is null and codigo_hash is not null;
  if not found then
    return json_build_object('error', 'Este usuario no tiene una activación pendiente.');
  end if;
  if p.codigo_intentos >= 5 then
    return json_build_object('error', 'Código bloqueado. Pide uno nuevo a coordinación.');
  end if;
  if p.codigo_hash <> crypt(p_codigo, p.codigo_hash) then
    update personas set codigo_intentos = codigo_intentos + 1 where id = p_persona;
    return json_build_object('error',
      case when p.codigo_intentos + 1 >= 5 then 'Código bloqueado. Pide uno nuevo a coordinación.'
           else format('Código incorrecto. Te quedan %s intentos.', 4 - p.codigo_intentos) end);
  end if;
  return json_build_object('ok', true);
end $$;

-- Paso 1 de la activación: ¿el código es correcto? (antes de pedir el PIN)
create or replace function verificar_codigo(p_persona text, p_codigo text)
returns json language sql security definer set search_path = public as $$
  select _revisar_codigo(p_persona, p_codigo);
$$;

-- Paso 2: con el código otra vez y el PIN nuevo, activa y abre sesión. Devuelve {token} o {error}.
create or replace function activar_usuario(p_persona text, p_codigo text, p_pin text)
returns json language plpgsql security definer set search_path = public, extensions as $$
declare
  r json := _revisar_codigo(p_persona, p_codigo);
  t uuid;
begin
  if r->>'error' is not null then
    return r;
  end if;
  if not _pin_seguro(p_pin) then
    return json_build_object('error', 'Elige un PIN menos obvio (sin repetir ni seguir números).', 'pin', true);
  end if;
  update personas set pin_hash = crypt(p_pin, gen_salt('bf')), codigo_hash = null, codigo_intentos = 0 where id = p_persona;
  insert into sesiones (persona_id) values (p_persona) returning token into t;
  return json_build_object('token', t);
end $$;

revoke execute on function _validar_datos(text, text, text), _pin_seguro(text), _codigo_nuevo(),
  _revisar_codigo(text, text) from public, anon, authenticated;
grant execute on function listar_pendientes(), listar_usuarios(uuid), crear_persona(uuid, text, text, text, text),
  reiniciar_acceso(uuid, text), verificar_codigo(text, text), activar_usuario(text, text, text) to anon, authenticated;

-- ===== migraciones/004_no_es_rosa_y_fotos_confirmadas.sql =====
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
