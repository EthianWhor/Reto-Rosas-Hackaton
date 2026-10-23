# Robot — detección por sectores y dashboard

El robot recorre el campo por sectores, detecta con la red neuronal los botones listos para cortar
y envía un reporte a un dashboard que ven:
- **los coordinadores**, para entender el estado del campo y organizar al personal;
- **una pantalla a la entrada del campo**, para que los operarios sepan en qué sectores enfocarse.

El objetivo es detectar los botones a tiempo, antes de que se abran demasiado y se pierdan, y
optimizar el tiempo de los operarios.

## Red neuronal: RosaNet (`ml/`)

CNN propia (`ml/model.py`, ~1,2 M parámetros, entrenada desde cero) que clasifica la
**etapa de apertura** de una rosa en la escala común definida en `ml/stages.py`:

1. Botón cerrado · 2. Apertura inicial · 3. Abierta · 4. Senescente

> Pendiente: alinear la escala con el proceso estándar de la finca (muy pronto / punto óptimo /
> muy tarde). Ver CONTEXTO.md.

Para cada predicción devuelve la etapa, la confianza, si está "segura" y tips. Opcionalmente
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

### 2. Descargar los datasets (formato **YOLOv8**) en `robot/descargas/`

| Dataset | Link | Clases |
|---|---|---|
| Rose (Sanjay M) | https://universe.roboflow.com/sanjay-m-7nbqj/rose-tk4yv | bud, mid-bud, flower |
| 食用玫瑰花期检测 (etapas de floración) | https://universe.roboflow.com/yolo-lmnpo/-zkger | 1_Bud, 2_Early_Bloom, 3_Full_Bloom, 4_Senescence |
| Rose Growth Stage (Mendeley) | https://data.mendeley.com/datasets/53vyvz5yyk/1 | Early, Middle, Final (carpetas) |

De cada proyecto de Roboflow descarguen **una sola versión** (las versiones repiten las mismas fotos).

### 3. Preparar, entrenar, evaluar y predecir

```bash
python -m ml.prepare_data --yolo descargas/rose --yolo descargas/floracion --folder descargas/mendeley --out data/stages
python -m ml.train --data data/stages --out runs/rosanet --epochs 40
python -m ml.evaluate --ckpt runs/rosanet/best.pt --data data/propias
python -m ml.predict --ckpt runs/rosanet/best.pt foto.jpg --cam mapa.jpg
```

`data/propias` es una carpeta con fotos propias de rosas comerciales, organizadas en una
subcarpeta por etapa (mismos nombres que en `ml/stages.py`). Es la prueba más honesta.

### Pruebas

```bash
python -m pytest
```
