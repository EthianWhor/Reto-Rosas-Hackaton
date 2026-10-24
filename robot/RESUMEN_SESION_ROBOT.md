# Resumen del trabajo en el robot y por dónde seguir

Fecha: 2026-10-24. Rama: **A** (repo `EthianWhor/Reto-Rosas-Hackaton`).
Para seguir en otra sesión: leer este archivo y después `PLAN_robot_rosas_X2.md` (el plan, siempre al día).

---

## 1. Reglas de trabajo (importante)

- **Solo se trabaja la parte del robot.**
  - La app de la tablet (`app-tablet/`) y Supabase son de otra persona: **no se tocan**.
  - El modelo (`robot/ml/`, `robot/modelos/`, `robot/CLAUDE.md`) es de otro compañero: **no se tocan sus archivos**. Si algo hay que adaptar, se adapta del lado del robot.
- **Los commits van a la rama `A`**, nunca a `main`.
  - Autor: la cuenta de la usuaria, sin cambiar la configuración global de git:
    `git -c user.name="noygomez076" -c user.email="noygomez076@gmail.com" commit ...`
  - El mensaje termina con `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
  - **Preguntar antes de cada commit/push.**
- **Cuando el equipo sube un modelo nuevo:**
  1. `git fetch` y `git merge origin/main` dentro de `A`.
  2. Comprobar que sus archivos quedaron idénticos (`git diff origin/main HEAD -- robot/ml robot/modelos app-tablet` vacío).
  3. Medir con `--rosas cartel` y adaptar el robot.
- **El modelo no está terminado.** RosaNet va a mejorar, así que lo que depende de cómo se equivoca la red se deja para el final.
- **A la usuaria le gusta ver la simulación:** abrir con `--ventana` cuando se termina algo.

## 2. Cómo correr

Desde `robot/`, con el entorno virtual de la raíz del repo (`.venv`, Python 3.14):

```bash
../.venv/Scripts/python.exe -X utf8 main.py                  # ronda de prueba (2 camas de 10 m)
../.venv/Scripts/python.exe -X utf8 main.py --ventana        # lo mismo, mirando el visor
../.venv/Scripts/python.exe -X utf8 main.py --rosas cartel   # con fotos reales: usa detector + RosaNet
../.venv/Scripts/python.exe -X utf8 main.py --completo       # invernadero completo (20 camas de 30 m)
../.venv/Scripts/python.exe -X utf8 main.py --bateria 30     # sale con 30 %: vuelve a la base al 25 %
../.venv/Scripts/python.exe -X utf8 main.py --continuar      # sigue la última ronda a medias
../.venv/Scripts/python.exe -X utf8 main.py --modo real      # lista lo que falta para el robot real
../.venv/Scripts/python.exe -X utf8 modo_foto.py --webcam    # demo en vivo con la webcam
../.venv/Scripts/python.exe -X utf8 -m pytest -q             # pruebas (133 al cerrar esta sesión)
```

En PowerShell: `..\.venv\Scripts\activate` y después `python main.py ...`.

Salidas en `robot/datos/` (no se sube a git):
- `rondas/<id>/`: fotos, detecciones, checkpoint.
- `salida/`: reporte Excel y JSON.
- `logs/`: log de cada ronda.
- `dashboard_simulado/`: lo "enviado".

## 3. Lo que ya está hecho (commits en la rama A)

| Commit | Qué |
|---|---|
| (pasos 1–5) | Simulación MuJoCo del X2 Ultra, camas y rosales, 4 posturas por parada, geometría píxel→3D, sin repetir rosas, madurez y "lista mañana", reporte Excel (6 hojas) + JSON con el formato de `app-tablet/src/data/reporte.ts`, envío con bandeja de salida y reintentos (carpeta / API / Supabase) |
| `c3b5673` | Ronda en serpiente desde la base y de vuelta, checkpoint (`--continuar`, `--parar-despues`), RosaNet "noche", envío a Supabase |
| `a9fd65d` | Modo foto para la demo (foto o webcam, cuadro guía, mini reporte) |
| `f05389c` | Escena realista (postes, alambres, mangueras, desniveles), sensor de obstáculos por rayos, frena y espera 30 s, abandona el camino si no lo quitan y lo reporta |
| `c615d43` | Acción física: apunta la cabeza a cada óptima y la ilumina con un foco (`accion.tipo: senalar`) |
| `d57646f` | Esqueleto del robot real `cuerpo/real_backend.py` con los tópicos del SDK AimDK_X2 (ROS 2) |
| `ade59cb` | Merge de `main`: detector ajustado con escenas de la finca |
| `25bccc6` | Adaptación al detector nuevo: mira la foto sin achicarla (`percepcion.detector_tamano_nativo`) |
| `2fdab32` | Log de cada ronda en `datos/logs/` y vuelta a la base por batería (25 %) |
| `bdd92fe` | Análisis de las fotos en otro hilo mientras camina, con checkpoint seguro |
| (paso 9, a medias) | Invernadero completo: física liviana, fotos con lo cercano, `--completo` (sección 4) |

**Números clave (simulación):**
- **Con oráculo (escena de prueba):** cobertura 90 %, 0 rosas falsas, 0 repetidas, error de altura < 1 cm.
- **Con fotos reales y el modelo del equipo (`--rosas cartel`):**
  - Cobertura 71 % y clase correcta 69 %.
  - De 12 "cortar hoy", 9 son óptimas, 2 inmaduras y 1 pasada.
  - Lo que falla es de RosaNet: se le escapan óptimas, y las pasadas casi siempre van a "dudosa".
- **Análisis en paralelo:** la ronda pasa de 62 s a 52 s, con el mismo reporte.
- **Batería:** una ronda de prueba gasta ~10 %. Con `--bateria 30` vuelve a las 13 paradas y con `--continuar` termina (cobertura 92 %).

## 4. Paso 9, invernadero a escala completa (terminado)

**Resultado (plan, sección 4.5):** 6.031 rosas, cobertura 95 %, 0 duplicados, 0,4 % falsas.
- Sin señalar: 2 h de robot, 1 vuelta a la base por batería.
- Señalando cada óptima: 4 h 46 min, 2 vueltas (~5,3 s por rosa): no cabe en una noche con una batería.
- **Decidido: señalar solo en los 10 primeros cuadrantes** del `orden` del último reporte
  (`accion.primeros_cuadrantes: 10`): **2 h 18 min, 1 vuelta, 211 rosas señaladas.** La primera noche, sin reporte
  anterior, señala en todos.
- Los 120 cuadrantes salen prioridad `alta` (umbral de 3 óptimas): hay que acordarlo con la finca.
- El visor muestra todo (52.486 piezas; MuJoCo 3.17 admite 100.000).
- Detector "noche" del equipo integrado (merge `3023aae`): en la simulación mide igual que el de día (plan 7.12).

Cambios de código del paso 9 (commit "paso 9 a medias"):
- `sim/escena_invernadero.py`: arma **dos modelos**.
  - Uno completo, para la cámara, el sensor y el visor.
  - Uno liviano, para la física: robot, piso y camas.
  - Con 52.000 piezas, caminar era 10 veces más lento. Ahora 1,25 m tarda 0,31 s de cómputo, igual que en la escena chica.
- `cuerpo/sim_backend.py`:
  - Camina con el modelo liviano y copia la pose al completo antes de cada foto o rayo (`_al_completo`).
  - El renderer dibuja todas las piezas (`max_geom`); antes faltaban rosas en las fotos.
  - En cada foto solo dibuja lo que está a menos de 6 m de la cámara: de 1,2 s a 0,12 s por foto, con la misma profundidad.
- `sim/rosas.py` y `sim/estructura.py`: las plantas y la estructura van en cuerpos `rosales` y `estructura`.
- `main.py`:
  - `--completo`.
  - Muestra el tiempo del robot (simulado), también en la hoja Ronda.
  - Dice "Invernadero" o "Invernadero de prueba" según el tamaño.
- `ronda.py`: el checkpoint guarda el tamaño del invernadero, así `--continuar` arma el mismo.
- `tests/test_escala.py`: pruebas nuevas. Pasan todas.

**Comprobado:** la ronda de prueba da exactamente el mismo reporte que antes (84 fotos, 90 %, 53/3/8).

Rondas completas medidas: `INV1_2026-10-24_044859` (señalando) e `INV1_2026-10-24_082220` (sin señalar). La ronda
`INV1_2026-10-24_045226` quedó cortada y se puede borrar.

## 5. Por dónde empezar en la próxima sesión

**Paso 10 terminado:** `DEMO.md` (guion de la demo, números para el pitch, límites y preguntas del jurado) y el
README del robot al día. RosaNet + forma medida con carteles (plan 7.13): 74–80 % de clase correcta y 0
inmaduras para "cortar hoy".

**Paso 3 terminado (plan 2.6):** si el modelo dice óptimo pero la cabeza mide menos de 3,5 cm o más de 8 cm, la
rosa va a dudosa; las dudosas que parecen óptimas suman a la prioridad del cuadrante. Las pasadas en "cortar hoy"
bajan de 6–7 a 0–3, sin perder óptimas. Umbrales "A CALIBRAR" con rosas reales.

**Envío a la app probado contra Supabase real** (2026-10-24): la clave está en `robot/.env` (no se sube), el
reporte llegó a la tabla `reportes` y las 29 fotos de dudosas se abren por su URL pública. Falta verlo en la tablet.
`main` tiene todo hasta `cdbe4f8` (merge fast-forward de A).

1. **X2 real (opcional, preparado):** `puente_x2.py` + `modo_foto.py --robot` (DEMO.md 2b). Probado sin robot (puente local con una foto de la finca); falta probarlo con el X2 delante.
2. **Siguiente paso, si hay tiempo:**
   - **Paso 7, "lista mañana" con historia:** reconocer la misma rosa de una noche a otra por su posición, medir cuánto creció y calcular los días que faltan. `percepcion/madurez.py` ya acepta `diametro_ayer_cm`.
3. **Pendiente de otras personas:**
   - **Equipo del modelo:**
     - con RosaNet + forma, las pasadas salen como óptimas (en la sim, 6–7 por ronda; la regla del tamaño del robot las baja a 0–3, plan 2.6);
     - medir el detector a 1280–1920 px con sus escenas (el robot rinde más así).
   - **Equipo:** la acción física quedó en apuntar e iluminar las óptimas de los 10 primeros cuadrantes; en el X2 real falta el foco.
   - **AgiBot / robot real:** ver `PLAN_robot_rosas_X2.md` sección 14.1.
     - La cámara es de 1280 × 720 (cobertura simulada 68 %).
     - En el X2 Ultra original la cabeza no se inclina.
     - Cabeza y caminar van en modos distintos, y la cintura solo tiene control de bajo nivel.
     - No hay foco en la cabeza.
     - La posición necesita el SLAM opcional.

## 6. Mapa rápido del código del robot

| Archivo | Qué hace |
|---|---|
| `main.py` | Arranca la ronda, reporte, métricas, envío |
| `ronda.py` | Serpiente, paradas, obstáculos, batería, análisis en paralelo, señalar, checkpoint |
| `registro.py` | Log en `datos/logs/` |
| `modo_foto.py` | Demo con foto o webcam |
| `reporte/fotos.py` | Fotos de las dudosas a Supabase Storage |
| `config/demo.yaml` | Config de la demo con la app (cartel + Supabase) |
| `DEMO.md` | Guion de la demo y números para el pitch |
| `puente_x2.py` | Va en el X2 real: cámara de la cabeza y LED del pecho para el modo foto (`--robot`) |
| `cuerpo/interfaz.py` | Lo que la ronda le pide al robot (igual en sim y real) |
| `cuerpo/sim_backend.py` | Robot en MuJoCo |
| `cuerpo/real_backend.py` | Esqueleto del X2 real (SDK AimDK_X2) |
| `cuerpo/posturas.py` | Las 4 posturas |
| `sim/escena_invernadero.py`, `sim/rosas.py`, `sim/estructura.py` | Escena |
| `navegacion/` | Plano y ruta |
| `percepcion/` | Candidatas, clasificador, geometría, sin repetir, madurez, uso del modelo del equipo |
| `reporte/` | Tabla, Excel/JSON, envío |
| `metricas.py` | Comparación contra la verdad de la simulación |
| `config/config.yaml` | Todos los parámetros |
| `PLAN_robot_rosas_X2.md` | El plan con todo lo medido y decidido |
