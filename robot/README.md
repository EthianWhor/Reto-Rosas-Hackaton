# Robot — detección por sectores y dashboard

El robot recorre el campo por sectores, detecta con la red neuronal los botones listos para cortar
y envía un reporte a un dashboard que ven:
- **los coordinadores**, para entender el estado del campo y organizar al personal;
- **una pantalla a la entrada del campo**, para que los operarios sepan en qué sectores enfocarse.

El objetivo es detectar los botones a tiempo, antes de que se abran demasiado y se pierdan, y
optimizar el tiempo de los operarios.

## Red neuronal: RosaNet (`ml/`)

CNN propia (`ml/model.py`, ~1,2 M parámetros, entrenada desde cero) que clasifica cada rosa
en las **3 categorías del proceso estándar de la finca** (`ml/stages.py`):

1. Inmaduro – no cortar · 2. Punto óptimo de corte (punto 3) · 3. Pasado / sobreabierto

Para cada predicción devuelve la categoría, la confianza, si está "segura" y tips basados en la
información técnica de la finca. Opcionalmente
genera un mapa de calor (Grad-CAM) con las zonas de la rosa que más pesaron en la decisión.

Todos los comandos se ejecutan **desde esta carpeta (`robot/`)**.

### 1. Instalar

En el portátil donde se armó el proyecto ya existe un entorno en la raíz del repo
(`..\.venv\Scripts\python`). En otro equipo:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
pip install -r requirements.txt
```

### 2. Datos de la finca (verdad de terreno)

Descomprimir `General.zip` en `robot/descargas/General` y convertir los círculos de los PDF en cajas YOLO:

```bash
python -m ml.finca_labels --src descargas/General --out data/finca_yolo
```

Revisen las cajas en `data/finca_yolo/preview/`. Las fotos de "Casos difíciles" quedan en test.

### 3. Datasets públicos de apoyo (formato **YOLOv8**) en `robot/descargas/`

| Dataset | Link | Clases |
|---|---|---|
| Rose (Sanjay M) | https://universe.roboflow.com/sanjay-m-7nbqj/rose-tk4yv | bud, mid-bud, flower |
| 食用玫瑰花期检测 (etapas de floración) | https://universe.roboflow.com/yolo-lmnpo/-zkger | 1_Bud, 2_Early_Bloom, 3_Full_Bloom, 4_Senescence |
| Rose Growth Stage (Mendeley) | https://data.mendeley.com/datasets/53vyvz5yyk/1 | Early, Middle, Final (carpetas) |

De cada proyecto de Roboflow descarguen **una sola versión** (las versiones repiten las mismas fotos).

### 4. Preparar, entrenar, evaluar y predecir

```bash
python -m ml.prepare_data --yolo data/finca_yolo --yolo descargas/rose --yolo descargas/floracion --folder descargas/mendeley --out data/stages
python -m ml.train --data data/stages --out runs/rosanet --epochs 40
python -m ml.evaluate --ckpt runs/rosanet/best.pt --data data/propias
python -m ml.predict --ckpt runs/rosanet/best.pt foto.jpg --cam mapa.jpg
```

`data/propias` es una carpeta con fotos propias de rosas comerciales, organizadas en una
subcarpeta por categoría (mismos nombres que en `ml/stages.py`). Es la prueba más honesta.

Para medir solo con las rosas de la finca que el modelo nunca vio:

```bash
python -m ml.prepare_data --yolo data/finca_yolo --out data/finca_stages
python -m ml.evaluate --ckpt runs/rosanet/best.pt --data data/finca_stages/test
```

### Pruebas

```bash
python -m pytest
```

## Ronda del robot (simulación en MuJoCo)

El plan completo está en [PLAN_robot_rosas_X2.md](PLAN_robot_rosas_X2.md). Se corre desde esta carpeta:

Primero se activa el entorno de la raíz del repo (ahí están instaladas las dependencias):

```bash
..\.venv\Scripts\activate
python main.py              # recorre el camino 1, ubica las rosas y arma el reporte Excel + JSON en datos/salida/
python main.py --ventana    # lo mismo, mirando el visor de MuJoCo
python main.py --camino 0   # otro camino (0 = la orilla)
python main.py --revisar    # solo revisa todo y toma una foto de prueba, sin caminar
```

La configuración está en `config/config.yaml`. Con `percepcion.candidatas: auto` y
`percepcion.clasificador: auto`, el robot usa lo que haya en `ml/`: hoy RosaNet, y el detector del
equipo en cuanto exista el módulo y los pesos que dice `modelo_equipo.detector` (después de un
`git pull` y de copiar los pesos, que no se suben a git). Todo lo que toca `ml/` está en
`percepcion/modelo_equipo.py`.

Cada ronda deja sus fotos y resultados en `datos/rondas/<id>/` (fotos con profundidad, detecciones, rosas sin
repetir y métricas contra la verdad de la simulación), y el reporte para el dashboard en `datos/salida/`
(`reporte_INV1_<fecha>.xlsx` con 6 hojas y `.json` con los mismos datos). Nunca sobreescribe: si ya hay un
reporte de esa noche, guarda `_v2`, `_v3`…
