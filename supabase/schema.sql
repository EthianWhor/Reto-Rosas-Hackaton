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

drop table if exists rondas_juego, cuadrantes_hechos, asistencia, config_turno, reportes, sesiones, personas,
  version_personas cascade;

-- ---------------------------------------------------------------- tablas

create table personas (
  id text primary key default 'p-' || substr(md5(random()::text), 1, 10),
  nombre text not null,
  rol text not null check (rol in ('admin', 'trabajador')),
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
  ('t-01',    'Marta',        'trabajador', extensions.crypt('1001', extensions.gen_salt('bf'))),
  ('t-02',    'Luis',         'trabajador', extensions.crypt('1002', extensions.gen_salt('bf'))),
  ('t-03',    'Ana',          'trabajador', extensions.crypt('1003', extensions.gen_salt('bf'))),
  ('t-04',    'Carlos',       'trabajador', extensions.crypt('1004', extensions.gen_salt('bf'))),
  ('t-05',    'Diana',        'trabajador', extensions.crypt('1005', extensions.gen_salt('bf'))),
  ('t-06',    'Jorge',        'trabajador', extensions.crypt('1006', extensions.gen_salt('bf'))),
  ('t-07',    'Paola',        'trabajador', extensions.crypt('1007', extensions.gen_salt('bf'))),
  ('t-08',    'Andrés',       'trabajador', extensions.crypt('1008', extensions.gen_salt('bf'))),
  ('t-09',    'Sandra',       'trabajador', extensions.crypt('1009', extensions.gen_salt('bf'))),
  ('t-10',    'Wilson',       'trabajador', extensions.crypt('1010', extensions.gen_salt('bf')));

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
