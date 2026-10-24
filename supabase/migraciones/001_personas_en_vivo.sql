-- 001: avisar en vivo cuando cambia la lista de personas (2026-10-24).
-- Se corre una sola vez sobre una base creada con schema.sql anterior a este cambio. No borra datos.
-- (schema.sql ya lo incluye para bases nuevas.)
--
-- La tabla personas no se puede leer con la clave anon (tiene el PIN cifrado), así que Realtime no
-- puede avisar sus cambios a la app. En su lugar, cada cambio en personas sube un contador en
-- version_personas, que sí es pública y está en Realtime; la app lo escucha y recarga la lista.

create table if not exists version_personas (
  id int primary key default 1 check (id = 1),
  version bigint not null default 0,
  actualizado timestamptz not null default now()
);
insert into version_personas (id) values (1) on conflict (id) do nothing;

alter table version_personas enable row level security;
drop policy if exists lectura on version_personas;
create policy lectura on version_personas for select to anon, authenticated using (true);
alter publication supabase_realtime add table version_personas;

create or replace function _tocar_personas()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  update version_personas set version = version + 1, actualizado = now() where id = 1;
  return null;
end $$;
revoke execute on function _tocar_personas() from public, anon, authenticated;

drop trigger if exists personas_cambian on personas;
create trigger personas_cambian after insert or update or delete on personas
  for each statement execute function _tocar_personas();
