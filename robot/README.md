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

| Dataset | Versión | Carpeta | Clases |
|---|---|---|---|
| [Rose (Sanjay M)](https://universe.roboflow.com/sanjay-m-7nbqj/rose-tk4yv/dataset/1/download/yolov8) | v1 | `descargas/rose` | bud, mid-bud, flower |
| [食用玫瑰花期检测 (floración)](https://universe.roboflow.com/yolo-lmnpo/-zkger/dataset/8/download/yolov8) | v8 | `descargas/floracion` | 1_Bud, 2_Early_Bloom, 3_Full_Bloom, 4_Senescence |

Descargar **una sola versión** de cada uno (las versiones repiten las mismas fotos). La v1 de Rose trae
copias en gris; `prepare_data` las descarta. El dataset de Mendeley **no se usa**: sus fotos son
escenas con rosas en varias etapas bajo una sola etiqueta.

### 4. Entrenar RosaNet (dos etapas)

Las clases intermedias de los datasets públicos (`mid-bud`, `2_Early_Bloom`) son rosas más abiertas
que el punto óptimo de la finca: mezclarlas directo con la finca enseña un criterio equivocado
(probado: 25 % de exactitud en rosas de la finca). Por eso:

```bash
# Recortes de la finca (3 categorías) y públicos (escala propia: botón / abriendo / abierta / senescente)
python -m ml.prepare_data --yolo data/finca_yolo --out data/finca_stages --pad 0.15
python -m ml.prepare_data --escala publica --yolo descargas/rose --yolo descargas/floracion --out data/pre

# Etapa 1: preentrenar desde cero con los públicos (aprende a "ver" rosas)
python -m ml.train --data data/pre --out runs/rosanet_pre --epochs 40 --batch-size 64 --workers 4

# Etapa 2: calibrar con la finca + validación cruzada por foto -> runs/rosanet/best.pt
# (--oscuro 0.5: aumento de fondo oscuro para que funcione de noche; ver robot/CLAUDE.md)
python -m ml.calibrate --init runs/rosanet_pre/best.pt --freeze 0 --oscuro 0.5 --out runs/rosanet
```

### 5. Entrenar el detector (YOLO11n preentrenado, una clase "rosa")

```bash
# 1) Base con los datasets públicos
python -m ml.prepare_detector --yolo descargas/rose --yolo descargas/floracion --out data/detector
python -m ml.train_detector --data data/detector/data.yaml --epochs 35 --batch 16

# 2) Ajuste con escenas del invernadero (todas las rosas marcadas en Roboflow, ver ml/preanotar.py)
python -m ml.preanotar --finca data/finca_yolo --video "descargas/General/Videos de apoyo/Video 1 vista a un lado.mp4" --out data/preanotadas
#    -> subir a Roboflow, corregir, exportar YOLOv8 en descargas/rosas_finca
python -m ml.prepare_detector --finca descargas/rosas_finca --repetir 8 --yolo descargas/rose --yolo descargas/floracion --max-publico 500 --out data/detector_finca
python -m ml.train_detector --data data/detector_finca/data.yaml --weights modelos/detector_rosas.pt --epochs 15 --imgsz 960 --batch 4 --patience 6 --name detector_finca

# 3) Versión "noche": + copias nocturnas simuladas de las escenas (--noche) y fotogramas de otro invernadero
python -m ml.prepare_detector --finca descargas/rosas_finca --repetir 6 --noche 6 --yolo descargas/rose --yolo descargas/floracion --yolo "descargas/night_roses::video" --max-publico 400 --out data/detector_noche
python -m ml.train_detector --data data/detector_noche/data.yaml --weights modelos/detector_rosas_dia.pt --epochs 15 --imgsz 960 --batch 4 --patience 6 --name detector_noche
```

`data/finca_yolo` (solo algunas rosas marcadas por escena) **no** se usa para el detector; las escenas
con **todas** las rosas marcadas (`descargas/rosas_finca`) sí.

### 6. Operar (modelos ya entrenados en `modelos/`)

El repo incluye los modelos entrenados, así que para usarlos no hace falta entrenar ni descargar datasets:

| Archivo | Qué es |
|---|---|
| `modelos/rosanet.pt` | RosaNet preentrenada + calibrada con la finca (inmaduro / óptimo / pasado) |
| `modelos/detector_rosas.pt` | YOLO11n ajustado para encontrar rosas (una clase) |
| `modelos/rosanet_calibracion.json` | Métricas de la validación cruzada con la finca |

```bash
# Una rosa recortada (+ mapa de calor de dónde miró la red)
python -m ml.predict foto.jpg --cam mapa.jpg
# Fotos de escena de un sector -> reporte JSON para el dashboard + fotos anotadas
python -m ml.pipeline --sector B3 "fotos/b3/*.jpg" --out reportes/b3.json --anotadas reportes/b3
# Medir con fotos propias organizadas por categoría
python -m ml.evaluate --ckpt modelos/rosanet.pt --data data/propias
```

Si se reentrena, copiar el resultado a `modelos/` (`runs/rosanet/best.pt` → `modelos/rosanet.pt`,
`runs/detector_finca/weights/best.pt` → `modelos/detector_rosas.pt`).

### Resultados (2026-10-23)

Ver `CONTEXTO.md`, sección 2.0.3.

### Pruebas

```bash
python -m pytest
```

## Ronda del robot (simulación en MuJoCo)

El plan completo está en [PLAN_robot_rosas_X2.md](PLAN_robot_rosas_X2.md). Se corre desde esta carpeta:

Primero se activa el entorno de la raíz del repo (ahí están instaladas las dependencias):

```bash
..\.venv\Scripts\activate
python main.py              # sale de la base, recorre los caminos en serpiente, vuelve y arma el reporte en datos/salida/
python main.py --ventana    # lo mismo, mirando el visor de MuJoCo
python main.py --camino 1   # solo un camino (0 = la orilla)
python main.py --parar-despues 5   # simula batería baja: para tras 5 paradas y vuelve a la base
python main.py --continuar         # sigue la última ronda que quedó a medias, sin repetir fotos
python main.py --revisar    # solo revisa todo y toma una foto de prueba, sin caminar
```

La escena tiene postes, alambres, mangueras y desniveles, y dos obstáculos de ejemplo (`sim.obstaculos` en el
config): una caja que alguien quita mientras el robot espera y un balde que bloquea un camino. El robot los ve
con un sensor de rayos (como un LiDAR): pasa despacio sobre lo bajo, frena ante lo alto, espera hasta 30 s y, si
sigue ahí, abandona ese camino y lo anota en el reporte.

Las fotos se analizan en otro hilo mientras el robot sigue posando y caminando (`percepcion.analisis_en_paralelo`);
una parada queda como hecha en el checkpoint recién cuando se analizaron sus fotos.

Log y batería: todo lo que sale en pantalla queda con la hora en `datos/logs/ronda_<id>.log`. Si la batería
baja del 25 %, el robot guarda el avance y vuelve a la base; después se sigue con `--continuar`. Para verlo:
`python main.py --bateria 30` (sale con 30 %).

Robot real: `cuerpo/real_backend.py` es el esqueleto para el AgiBot X2 Ultra con el SDK AimDK_X2 (ROS 2). Con
`modo: real` en el config, `python main.py` muestra qué falta probar en el robot (sección 14.1 del plan).

Acción física: después de las fotos de cada parada, el robot apunta la cabeza a cada rosa óptima nueva y la
ilumina con un foco angosto (`accion` en el config; `tipo: ninguna` lo apaga). Así el operario ve en el momento
qué rosas cortar. Cada rosa se señala una sola vez, aunque se vea desde dos paradas.

La configuración está en `config/config.yaml`. Con `percepcion.candidatas: auto` y
`percepcion.clasificador: auto`, el robot usa el modelo del equipo de `ml/` (detector + RosaNet, pesos en
`modelos/`, contrato en `CLAUDE.md`). Con las rosas de la simulación como figuras usa el oráculo; para que
el robot "piense" con el modelo de verdad, las rosas se ponen como carteles con fotos reales de la finca:

```bash
python main.py --rosas cartel
```

Todo lo que toca `ml/` está en `percepcion/modelo_equipo.py`.

Cada ronda deja sus fotos y resultados en `datos/rondas/<id>/` (fotos con profundidad, detecciones, rosas sin
repetir y métricas contra la verdad de la simulación), y el reporte para el dashboard en `datos/salida/`
(`reporte_INV1_<fecha>.xlsx` con 6 hojas y `.json` con los mismos datos). Nunca sobreescribe: si ya hay un
reporte de esa noche, guarda `_v2`, `_v3`…

**Envío al dashboard.** Durante la ronda no hay WiFi: los reportes esperan en `datos/salida/`. En la
simulación el WiFi "aparece" al volver a la base y se copian a la carpeta del dashboard
(`datos/dashboard_simulado/`); los enviados pasan a `datos/enviados/`. Si un envío falla, se reintenta
en 1, 2, 4, 8… min. Para el robot real, copiar `.env.ejemplo` como `.env`, poner la carpeta compartida o
la dirección del dashboard, y dejar corriendo:

```bash
python -m reporte.envio
```

## Modo foto: demo en vivo

El jurado trae una rosa o una foto, y el robot la analiza con el mismo pipeline de la ronda (detector del equipo
+ RosaNet + reglas del robot). Muestra la foto con cada rosa marcada por estado y, en la consola, los consejos de
la finca para reconocerla.

```bash
python modo_foto.py foto.jpg            # una o varias fotos
python modo_foto.py --webcam            # cámara en vivo: ESPACIO analiza, Q sale
python modo_foto.py foto.jpg --enviar   # además manda un mini reporte a la app (envio.metodo)
```

Las fotos anotadas quedan en `datos/modo_foto/`. Si la foto es de una sola rosa de cerca y el detector no la
encuentra, se analiza la foto completa como una rosa; con la cámara, solo lo que está dentro del cuadro guía del
centro. Sin profundidad no se predice "lista mañana".

