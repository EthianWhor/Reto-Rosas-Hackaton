-- 003: alta con código de activación; cada persona crea su propio PIN (2026-10-24).
-- Se corre una sola vez sobre una base con las migraciones 001 y 002. No borra datos.
--
-- Antes, la coordinación ponía el PIN de cada persona y por eso lo conocía. Ahora:
-- 1. La coordinación registra nombre, correo, teléfono y rol. La base genera un código de 6 dígitos
--    que se muestra UNA vez (se guarda cifrado) y se le entrega a la persona.
-- 2. La persona toca "Activar mi usuario", elige su nombre, escribe el código y crea su PIN (dos veces).
-- 3. Con 5 códigos equivocados se bloquea; la coordinación genera uno nuevo ("Reiniciar acceso").
--    "Reiniciar acceso" también sirve si alguien olvida su PIN: lo borra y da un código nuevo.
-- Los usuarios que ya existían conservan su PIN.

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
