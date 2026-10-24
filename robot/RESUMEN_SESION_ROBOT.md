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
../.venv/Scripts/python.exe -X utf8 -m pytest -q             # pruebas (118 al cerrar esta sesión)
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

**Números clave (simulación):**
- **Con oráculo (escena de prueba):** cobertura 90 %, 0 rosas falsas, 0 repetidas, error de altura < 1 cm.
- **Con fotos reales y el modelo del equipo (`--rosas cartel`):**
  - Cobertura 71 % y clase correcta 69 %.
  - De 12 "cortar hoy", 9 son óptimas, 2 inmaduras y 1 pasada.
  - Lo que falla es de RosaNet: se le escapan óptimas, y las pasadas casi siempre van a "dudosa".
- **Análisis en paralelo:** la ronda pasa de 62 s a 52 s, con el mismo reporte.
- **Batería:** una ronda de prueba gasta ~10 %. Con `--bateria 30` vuelve a las 13 paradas y con `--continuar` termina (cobertura 92 %).

## 4. En curso: paso 9, invernadero a escala completa (SIN commit todavía)

Estos cambios ya están en la carpeta local de la usuaria, pero **no tienen commit**:
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

**Se estaba corriendo** la ronda completa (`main.py --completo` y después `--continuar`).
- Log: `datos/logs/ronda_INV1_2026-10-24_044859.log`. Al escribir esto iba por el camino 7 de 21.
- Hay otra ronda completa empezada con ventana y cortada en el camino 0 (`INV1_2026-10-24_045226`): se puede borrar o seguir.

## 5. Por dónde empezar en la próxima sesión

1. **Terminar el paso 9.**
   - Leer el resultado de la ronda completa: log y `metricas.json` de la carpeta de la ronda. Si no terminó, correr `main.py --completo` (y `--continuar` si se corta por batería), en segundo plano.
   - Anotar en el plan (secciones 4.4 y 16):
     - tiempo del robot, cuántas veces volvió por batería, cobertura, rosas falsas y repetidas;
     - tamaño del reporte (120 cuadrantes) y tiempo de cómputo.
   - **Ojo:** con ~6.000 rosas, señalar cada óptima (~5 s por rosa) puede sumar horas a la ronda. Medirlo comparando `accion.tipo: senalar` contra `ninguna`, y si no cabe en la noche, proponer opciones: señalar solo en los cuadrantes de prioridad alta, bajar `accion.segundos`, o marcar con la tira LED sin apuntar.
   - Revisar si el visor (`--ventana`) muestra todas las rosas con el invernadero completo: el visor tiene su propio límite de 10.000 piezas.
   - Correr las pruebas y **preguntar** antes de hacer el commit en `A`.
2. **Paso 10: cierre para la presentación.** README del robot, guion de la demo (simulación + modo foto con webcam) y números para el pitch (cobertura, tiempo por noche, batería, obstáculos).
3. **Al final, cuando llegue el RosaNet completo** (hacer pull y medir con `--rosas cartel`):
   - **Paso 3, reglas de decisión:**
     - el tamaño de la cabeza como segunda opinión (si la red dice óptimo pero la cabeza es chica → dudosa);
     - contar en la prioridad las dudosas cuya mejor clase es óptimo.
     - Se dejó en pausa porque depende de cómo se equivoque la red.
   - **Paso 7, "lista mañana" con historia:** reconocer la misma rosa de una noche a otra por su posición, medir cuánto creció y calcular los días que faltan. `percepcion/madurez.py` ya acepta `diametro_ayer_cm`.
4. **Pendiente de otras personas:**
   - **Equipo del modelo:**
     - RosaNet "noche" deja escapar óptimas en recortes chicos (70–100 px);
     - las pasadas salen dudosas;
     - medir el detector a 1280–1920 px con sus escenas (el robot rinde más así).
   - **Equipo:** confirmar la acción física (hoy apunta e ilumina).
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
