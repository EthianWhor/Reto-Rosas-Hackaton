# App tablet — juego para mecanizar el proceso

App tipo juego en tablet que ayuda a los operarios a interiorizar el proceso estándar de la finca
hasta hacerlo de forma mecánica. Hecha con **Expo (SDK 58) + Expo Router + TypeScript**.

## Qué hay (base)

| Pantalla | Archivo | Estado |
|---|---|---|
| Ingreso: cada persona toca su nombre y escribe su PIN; menú según el rol | `src/app/index.tsx`, `src/componentes/Ingreso.tsx` | Listo |
| Lo que encontró el robot: orden de corte por cuadrante y lo que estará listo mañana, según el reporte JSON de la ronda | `src/app/hoy.tsx` | Listo (con reporte de ejemplo) |
| **Trabajador** · Mi turno de hoy: los cuadrantes que le tocan, en orden, con casilla para marcar cada uno como hecho | `src/app/mi-turno.tsx` | Listo |
| **Admin** · Turno de hoy: quién vino, duración del turno, reparto y avance de cada persona | `src/app/turno.tsx` | Listo |
| **Admin** · Trabajadores: agregar y quitar personas, con su PIN y su rol | `src/app/trabajadores.tsx` | Listo |
| Aprender las 3 categorías: fotos reales de la finca + qué mirar | `src/app/aprender.tsx` | Listo |
| Juego: clasifica el botón (muy pronto / punto óptimo / muy tarde) con explicación inmediata | `src/app/clasificar.tsx` | Listo (básico) |
| Mi progreso: aciertos por categoría y con qué la confunde | `src/app/progreso.tsx` | Listo (básico, solo en la tablet) |
| Sanación después del corte | `src/app/sanacion.tsx` | **Pendiente: falta el proceso de la finca** |

- Las categorías y los tips (`src/data/categorias.ts`) usan las mismas claves que RosaNet
  (`robot/ml/stages.py`). Si cambian allá, cambiarlas aquí.
- Las rondas reparten las fotos por categoría (hay 47 inmaduras, 20 óptimas y solo 2 pasadas), así
  que las de "muy tarde" se repiten.
- El progreso se guarda en la tablet con AsyncStorage.

## Correr en desarrollo

Requiere **Node 22.13 o superior** (Expo SDK 58 avisa que Node 20 ya no está soportado).

```bash
npm install
npm start          # escanear el QR con Expo Go en la tablet
npm run web        # o verla en el navegador
```

Todas las librerías actuales vienen incluidas en **Expo Go**, así que no hace falta compilar para
desarrollar. Solo hará falta un build propio (development build) si se agrega una librería nativa
que Expo Go no trae, por ejemplo correr RosaNet en la tablet (TFLite/ONNX) o el modo kiosco.

## Roles y reparto del turno

La tablet es compartida (va a la entrada del invernadero): cada persona entra con su nombre y su
PIN, y sale al terminar. Por seguridad, **la sesión no se guarda**: al abrir o recargar la app
siempre pide el PIN, y la sesión se cierra sola tras **3 minutos sin tocar la pantalla** o si la app
pasa a segundo plano (`src/logica/operario.tsx`).

- **Admin** (coordinación): marca quién vino, ajusta las horas de corte, los segundos por rosa y
  los minutos para llegar a un cuadrante, y ve el avance de todos.
- **Trabajador:** ve sus cuadrantes, los marca como hechos y practica (aprender, juego, progreso).

**Reparto** (`src/logica/turno.ts`): toma los cuadrantes con rosas en punto 3 del reporte del robot.
Si no alcanza el tiempo, se quedan los de mayor prioridad y el resto aparece como "no caben en el
turno". Los elegidos se ordenan por cama y tramo y se parten en **zonas seguidas** con más o menos
el mismo tiempo, para que cada persona trabaje en camas vecinas. Con los mismos datos, todos ven el
mismo reparto.

**Usuarios de prueba** (creados por `supabase/schema.sql`): Coordinadora (admin, PIN 1234) y 10
trabajadores (Marta 1001, Luis 1002 … Wilson 1010).

## Base de datos: Supabase

Todo se guarda en Supabase (esquema y reglas en [`../supabase/schema.sql`](../supabase/schema.sql)):
personas, sesiones, reportes del robot, configuración del turno, asistencia, cuadrantes hechos y
rondas del juego. Así varias tablets ven lo mismo y **los cambios llegan en vivo** (si Marta marca un
cuadrante, la pantalla de la coordinadora se actualiza sola).

- La app usa la URL y la clave pública (anon) de `app-tablet/.env`. Esa clave puede ir en el repo: con
  ella solo se **leen** los datos del turno. Todo lo que **escribe** pasa por funciones de la base que
  exigen una sesión abierta con nombre + PIN, y las de administración revisan que sea un admin.
- El PIN se guarda cifrado en la base y nunca llega a la app; la app solo recibe un token de sesión.
- Sin conexión: se ve el último reporte descargado y la lista de personas guardada; el juego guarda
  las rondas en la tablet. Marcar cuadrantes y entrar sí necesitan conexión.

## Reporte del robot

El turnero lee el último reporte de la tabla `reportes` (formato en `src/data/reporte.ts`, igual al
de `robot/reporte/archivos.py`). El robot lo sube con:

```bash
cd ../robot
python subir_reporte.py datos/salida/reporte_INV1_2026-10-24.json
```

(necesita `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` en `robot/.env`, que no se sube al repo).
Si todavía no hay reportes, la app muestra uno de ejemplo y lo dice abajo de la pantalla.

## Fotos de las rosas

Las fotos son los recortes de la finca que genera `robot/ml/prepare_data`. Para actualizarlas:

```bash
npm run fotos      # copia ../robot/data/finca_stages a assets/rosas y regenera src/data/rosas.ts
```

## Generar el APK (EAS)

```bash
npx eas-cli@latest login
npx eas-cli@latest init        # solo la primera vez: crea el proyecto en la cuenta de Expo
npm run build:apk              # perfil "preview" de eas.json → APK para instalar en la tablet
```

EAS no sube lo que esté en `.gitignore`, así que `assets/rosas` no debe ignorarse o las fotos no
entran en el APK.

## Pendiente
- Recibir de la finca el proceso de sanación (pasos, errores típicos, fotos o video).
- Definir cuándo y dónde se usa la tablet (los celulares no están permitidos en el cultivo).
- Más fotos de "pasado / sobreabierto".
