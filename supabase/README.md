# Supabase — base de datos de Punto 3

Proyecto: `fxlljandvphujxxddvxy` (https://fxlljandvphujxxddvxy.supabase.co). La comparten la app de la
tablet, el robot y, más adelante, las gafas (Meta Quest).

## Crear o reiniciar la base

1. Abrir el proyecto en supabase.com → **SQL Editor** → **New query**.
2. Pegar todo [`schema.sql`](schema.sql) y darle **Run**.

Se puede volver a correr cuando cambie el esquema, pero **borra los datos** y deja los usuarios de prueba.

Para cambiar una base que ya tiene datos, se corren los archivos de [`migraciones/`](migraciones/) que
falten, en orden. `schema.sql` siempre incluye todas las migraciones.

| Migración | Qué cambia | Aplicada en el proyecto |
|---|---|---|
| `001_personas_en_vivo.sql` | Tabla `version_personas` y disparador: la lista de personas se actualiza sola en todas las tablets | Sí (2026-10-24) |

## Qué hay

| Tabla | Qué guarda | Quién escribe |
|---|---|---|
| `personas` | Nombre, rol (admin / trabajador), PIN cifrado y `activo`. **Quitar no borra la fila**: la deja con `activo = false`, para no perder lo que la persona marcó o practicó | Admin, con `crear_persona` y `quitar_persona` |
| `version_personas` | Un contador que sube con cada cambio en `personas`, para avisar en vivo a la app | Disparador `personas_cambian` |
| `sesiones` | Token de cada sesión abierta (vence a las 14 h) | `entrar` y `salir` |
| `reportes` | JSON completo de cada ronda del robot | El robot (`robot/subir_reporte.py`, clave service_role) |
| `config_turno` | Horas de corte, segundos por rosa, minutos por cuadrante | Admin, con `guardar_config` |
| `asistencia` | Quién vino cada día | Admin, con `guardar_asistencia` |
| `cuadrantes_hechos` | Qué cuadrante marcó quién y cuándo | Trabajadores, con `marcar_hecho` |
| `rondas_juego` | Respuestas del juego de clasificación | Cada persona, con `guardar_ronda_juego` |

**Reglas:** con la clave pública (anon) solo se leen `reportes`, `config_turno`, `asistencia` y
`cuadrantes_hechos`. `personas`, `sesiones` y `rondas_juego` no se pueden leer directo. Todo lo que
escribe pasa por funciones que validan el token de sesión (y el rol, cuando hace falta).

**En vivo:** `cuadrantes_hechos`, `asistencia`, `config_turno`, `reportes` y `version_personas` están en
Realtime.

Para ver solo las personas activas en el Table Editor, filtrar `activo` = `true`.

## Claves

- **anon** (pública): va en `app-tablet/.env`.
- **service_role** (secreta): solo en `robot/.env`, para subir reportes. Nunca en la app ni en el repo.
