# RoseApp — app de la tablet

App de la tablet compartida a la entrada del invernadero: muestra el informe de la ronda nocturna del
robot, reparte el turno y, con un juego, ayuda a los operarios a interiorizar el proceso estándar de la
finca hasta hacerlo de forma mecánica. Hecha con **Expo (SDK 58) + Expo Router + TypeScript**.

Estilo: rosa, rojo y blanco, tipografía Nunito e íconos de Ionicons (`src/tema.ts`). Botones 3D
(`src/componentes/BotonGrande.tsx`) y animaciones con `Animated` de React Native
(`src/componentes/animaciones.tsx`): pétalos al acertar, sacudida al fallar, racha, puntos y
barras que se llenan. Todo funciona en Expo Go.

## Qué hay (base)

| Pantalla | Archivo | Estado |
|---|---|---|
| Ingreso: cada persona toca su nombre y escribe su PIN; menú según el rol | `src/app/index.tsx`, `src/componentes/Ingreso.tsx` | Listo |
| Informe del robot: orden de corte por cuadrante y lo que estará listo mañana, según el reporte JSON de la ronda | `src/app/hoy.tsx` | Listo (con reporte de ejemplo) |
| **Experto y aprendiz** · Mi turno de hoy: los cuadrantes que le tocan, en orden, con casilla para marcar cada uno como hecho | `src/app/mi-turno.tsx` | Listo |
| **Admin** · Turno de hoy: quién vino, duración del turno, reparto y avance de cada persona | `src/app/turno.tsx` | Listo |
| **Admin** · Usuarios: registrar (nombre, correo, teléfono, rol), promover, reiniciar acceso y quitar | `src/app/trabajadores.tsx`, `src/app/nuevo-usuario.tsx` | Listo |
| **Experto** · Rosas dudosas: responde las rosas en que el robot dudó (o "no es una rosa"), con la foto real, en vivo | `src/app/revisar.tsx` | Listo |
| Aprender las 3 categorías: fotos reales de la finca + qué mirar | `src/app/aprender.tsx` | Listo |
| Juego: clasifica el botón (muy pronto / punto óptimo / muy tarde) con explicación inmediata | `src/app/clasificar.tsx` | Listo (básico) |
| Mi progreso: aciertos por categoría y con qué la confunde | `src/app/progreso.tsx` | Listo (básico, solo en la tablet) |
| Corte y sanación: los 9 pasos, "ordena los pasos" y preguntas (¿qué está mal?, verdadero o falso) | `src/app/sanacion.tsx`, `src/data/sanacion.ts` | Listo (versión de trabajo, sale de la investigación en `contenido/corte-y-sanacion.md` y va alineada con la VR; falta confirmarla con la finca) |

- Las categorías y los tips (`src/data/categorias.ts`) usan las mismas claves que RosaNet
  (`robot/ml/stages.py`). Si cambian allá, cambiarlas aquí.
- Las rondas reparten las fotos por categoría (hay 47 inmaduras, 20 óptimas y solo 2 pasadas), así
  que las de "muy tarde" se repiten.
- El progreso se guarda en la tablet con AsyncStorage.
- **El material crece solo:** el juego y "Aprender" suman las fotos reales del robot que ya tienen
  categoría confirmada, sea por un experto en "Rosas dudosas" o por el robot cuando mandó a cortar con
  confianza ≥ 0,8 (`src/logica/confirmadas.ts`, `fotos_confirmadas()` en Supabase). En el juego llevan el
  sello "Foto del robot".

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

- **Coordinación** (`admin`): marca quién vino, ajusta las horas de corte, los segundos por rosa y
  los minutos para llegar a un cuadrante, ve el avance de todos y administra los usuarios: los crea
  y **promueve a experto** a quien termina la capacitación.
- **Experto** (`experto`): ve sus cuadrantes y **revisa las rosas dudosas** del robot (`src/app/revisar.tsx`);
  cada respuesta se guarda en `etiquetas_expertos` para reentrenar a RosaNet. No ve los juegos.
- **Aprendiz** (`aprendiz`, en capacitación): ve sus cuadrantes, aprende, practica con el juego y
  ve su progreso.

Las pantallas están protegidas por rol en `src/app/_layout.tsx` (`Stack.Protected`).

**Modo turnero** (`src/app/turnero.tsx`, `src/app/activar-turnero.tsx`, `src/logica/turnero.tsx`): para la
tablet fija de la entrada. Coordinación lo activa desde su inicio y elige un **código de salida de 6 números**
(dos veces; no acepta 111111 ni 123456). Desde ahí la tablet solo muestra el tablero del turno:
- El avance de todos en vivo y "¿Quién eres?" con cada persona presente y su avance.
- Al tocar su nombre, la persona ve su zona (camas) y sus cuadrantes en orden. Para marcar uno o "Terminé mi
  turno" escribe su PIN, así nadie marca por otro. Sin tocar la pantalla 1 minuto, vuelve al tablero y cierra
  esa sesión.
- No hay forma de llegar a otra pantalla: las demás rutas quedan bloqueadas, el botón atrás de Android no
  sale y al cerrar o recargar la app sigue en el turnero.
- Se sale con el candado de arriba y el código (5 intentos y espera de 1 minuto). Si nadie lo recuerda,
  alguien de coordinación sale con su PIN.
- El código se guarda en la tablet solo como huella. Para bloquear también el sistema (que no se pueda salir
  de la app), usar la fijación de pantalla de Android o el Acceso guiado de iPad.

**Alta y activación (nadie conoce el PIN de otro):** coordinación registra nombre, correo, teléfono y
rol, y recibe un **código de 6 números** que se muestra una sola vez. La persona toca "¿Eres nuevo?
Activa tu usuario", elige su nombre, escribe el código y **crea su PIN dos veces** (no se aceptan PIN
obvios como 1111 o 1234). Con 5 códigos equivocados se bloquea; coordinación da uno nuevo con
"Reiniciar acceso", que también sirve si alguien olvida su PIN (`src/componentes/Ingreso.tsx`,
`src/logica/cuentas.ts`, `supabase/migraciones/003`).

**Reparto** (`src/logica/turno.ts`): toma los cuadrantes con rosas en punto 3 del reporte del robot.
Si no alcanza el tiempo, se quedan los de mayor prioridad y el resto aparece como "no caben en el
turno". Los elegidos se ordenan por cama y tramo y se parten en **zonas seguidas** con más o menos
el mismo tiempo, para que cada persona trabaje en camas vecinas. Con los mismos datos, todos ven el
mismo reparto.

**Usuarios de prueba** (creados por `supabase/schema.sql`): Coordinadora (admin, PIN 1234) y 10
aprendices (Marta 1001, Luis 1002 … Wilson 1010). No hay expertos: para revisar las dudosas, promover a
alguien desde "Usuarios".

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

(necesita `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` en `robot/.env`, que ya está en git porque el
repo es privado).
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
- Confirmar con la finca el proceso de corte y sanación (preguntas al final de `contenido/corte-y-sanacion.md`) y ajustar `src/data/sanacion.ts`.
- Más fotos de "pasado / sobreabierto".
