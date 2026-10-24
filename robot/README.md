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

# Etapa 3: clasificador de forma y color (tipo plantilla) que se promedia con RosaNet
python -m ml.shape --out modelos/forma.joblib     # va junto a rosanet.pt; RosePredictor lo carga solo
python -m ml.shape_cv --runs runs/sweep_oscuro --prefijo o0.5-   # compara forma / RosaNet / combinadas

# --extra CARPETA suma rosas etiquetadas por otras personas solo al entrenamiento (la medición sigue
# siendo con la finca). Probado con las del equipo: de noche no ayudó (ver CONTEXTO.md).
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
