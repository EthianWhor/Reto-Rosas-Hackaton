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
| `002_roles_y_dudosas.sql` | Roles `admin` / `experto` / `aprendiz` (los "trabajador" pasan a aprendiz), `cambiar_rol` para promover, tabla `etiquetas_expertos` y funciones para revisar las dudosas del robot | Sí (2026-10-24) |
| `004_no_es_rosa_y_fotos_confirmadas.sql` | Respuesta "no es una rosa" en las dudosas (`categoria = 'no_rosa'`) y `fotos_confirmadas()`: fotos del robot clasificadas por un experto u óptimas con confianza ≥ 0,8, para el juego y "Aprender" | Sí (2026-10-24) |
| `003_activacion_con_codigo.sql` | Alta con nombre, correo, teléfono y rol; código de activación de 6 dígitos (cifrado, 5 intentos); cada persona crea su propio PIN (no obvio); "reiniciar acceso"; validación de nombre, correo y teléfono | Sí (2026-10-24) |

## Qué hay

| Tabla | Qué guarda | Quién escribe |
|---|---|---|
| `personas` | Nombre, rol (admin / experto / aprendiz), PIN cifrado y `activo`. **Quitar no borra la fila**: la deja con `activo = false`, para no perder lo que la persona marcó o practicó | Admin, con `crear_persona` y `quitar_persona` |
| `etiquetas_expertos` | Respuesta de un experto sobre una rosa en la que el robot dudó (ronda, rosa, cuadrante, categoría). Es verdad de terreno para reentrenar a RosaNet; el equipo del modelo la lee con la clave service_role | Expertos y coordinación, con `etiquetar_dudosa` |
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
- **service_role** (secreta, de administrador): solo en `robot/.env`, para subir reportes. Nunca en la app.
  `robot/.env` está en git a propósito porque el repo es privado (decisión del equipo, 2026-10-24): **el
  repo no se puede hacer público** sin antes cambiar esta clave en Supabase.
