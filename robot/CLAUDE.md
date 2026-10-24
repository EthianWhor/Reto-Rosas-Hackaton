# robot/ — contexto para trabajar aquí

Contexto general del reto y decisiones: `../CONTEXTO.md` (secciones 2.0.x). Detalle de
entrenamiento: `README.md`. Este archivo explica **cómo usar la red neuronal del equipo
(`ml/`) desde el código del robot**.

## Quién hace qué
- `ml/` es la red neuronal (detector + RosaNet). La mantiene otra persona del equipo: no cambiar
  su lógica sin coordinar. Si hace falta algo distinto, mejor adaptarlo del lado del robot.
- El código del robot (simulación, ronda, reporte, envío) usa `ml/` solo a través de lo que
  se describe abajo.

## Entorno
Todos los comandos se corren **desde `robot/`** (los imports son `from ml.… import …`).

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126   # sin GPU: pip install torch torchvision
pip install -r requirements.txt
```

## Modelos entrenados (ya están en git)
| Archivo | Qué hace |
|---|---|
| `modelos/detector_rosas.pt` | YOLO11n ajustado: encuentra **dónde** hay rosas en una foto de escena (una clase, "rosa") |
| `modelos/rosanet.pt` | RosaNet (CNN propia): dice si una rosa **recortada** está `1_inmaduro`, `2_optimo` o `3_pasado` |
| `modelos/rosanet_calibracion.json` | Métricas de la validación cruzada con las fotos de la finca |

No hace falta copiar pesos de `runs/` (eso era antes; `runs/` no está en git).

### Config del robot (`config/config.yaml`, sección `modelo_equipo`)
Estos son los nombres reales; reemplazan los "supuestos":

```yaml
modelo_equipo:
  clasificador:
    modulo: ml.predict
    clase: RosePredictor
    pesos: modelos/rosanet.pt
  detector:
    modulo: ml.detect
    clase: RoseDetector
    pesos: modelos/detector_rosas.pt
    clasifica: false        # el detector solo ubica; la categoría la da RosaNet
```

## API (contrato)

### Detector: `ml.detect.RoseDetector`
```python
from ml.detect import RoseDetector
det = RoseDetector("modelos/detector_rosas.pt")          # device=None -> GPU si hay
dets = det.detect(imagen)   # PIL.Image o np.ndarray RGB (H, W, 3)
# -> [{"bbox": [x1, y1, x2, y2], "confianza": 0.43}, ...]   (píxeles de la imagen, floats)
```
- **Ojo con OpenCV:** un `np.ndarray` se interpreta como **RGB**. Si viene de `cv2` (BGR),
  convertir antes: `cv2.cvtColor(img, cv2.COLOR_BGR2RGB)`.
- Parámetros ya ajustados con las fotos de la finca (constantes en `ml/detect.py`):
  `DET_CONF = 0.10`, `DET_IMGSZ = 1280`, `NMS_IOU = 0.5`, y se descartan cajas de más del 8 % de
  la foto (`MAX_BOX_FRACTION`; con conf baja aparecían cajas gigantes sobre el techo).

### Clasificador: `ml.predict.RosePredictor`
```python
from ml.predict import RosePredictor, DEFAULT_THRESHOLD   # DEFAULT_THRESHOLD = 0.6
from ml.prepare_data import pad_box
clf = RosePredictor("modelos/rosanet.pt")                  # threshold=0.6 por defecto
recorte = imagen.crop(pad_box([int(v) for v in bbox], *imagen.size, 0.15))   # 15 % de margen
r = clf.predict(recorte)    # PIL.Image de UNA rosa
# -> {"etapa": "2_optimo", "nombre": "Punto óptimo de corte", "confianza": 0.856, "seguro": True,
#     "probabilidades": {"1_inmaduro": 0.1, "2_optimo": 0.856, "3_pasado": 0.044},
#     "tips": {"mirar": [...], "diferencia": "..."}}
```
- `seguro` = `confianza >= 0.6`. Si es `False`, tratar la rosa como **dudosa / incierta**.
- Las etapas llevan prefijo de orden. Para las clases del robot (`inmaduro`, `optimo`, `pasado`):
  `clase = r["etapa"].split("_", 1)[1]`; igual con las llaves de `probabilidades`.
- **Margen del recorte: usar 15 %** (`pad=0.15`). Es el que usa el pipeline y con el que se
  calibró RosaNet. Si el config del robot tiene `margen_recorte: 0.10`, conviene subirlo a 0.15.
- `predict()` también trae `tips` (qué mirar en esa categoría, según la información técnica de
  la finca), por si el reporte o la pantalla los quieren mostrar.

### Atajo: detector + RosaNet juntos — `ml.pipeline.RoseInspector`
```python
from ml.pipeline import RoseInspector
ins = RoseInspector("modelos/detector_rosas.pt", "modelos/rosanet.pt")
rosas = ins.inspect(imagen_pil)
# -> [{"caja": [x1, y1, x2, y2], "confianza_deteccion": 0.43, "categoria": "2_optimo" | ... | "incierta",
#      "categoria_red": "2_optimo", "confianza": 0.86, "probabilidades": {...}}, ...]
```

## Comandos (desde `robot/`)
```bash
# Fotos de escena de un sector -> reporte JSON (conteo, listas para cortar, prioridad) + fotos anotadas
python -m ml.pipeline --sector B3 "fotos/b3/*.jpg" --out reportes/b3.json --anotadas reportes/b3
# Una rosa ya recortada (+ mapa de calor de dónde miró la red)
python -m ml.predict foto.jpg --cam mapa.jpg
# Medir con fotos propias organizadas en subcarpetas 1_inmaduro/ 2_optimo/ 3_pasado/
python -m ml.evaluate --ckpt modelos/rosanet.pt --data data/propias
# Pruebas (incluye una que verifica este contrato con los modelos de modelos/)
python -m pytest
```

## Rendimiento (medido el 2026-10-23)
- **Velocidad:** ~86 ms por foto con GPU (GTX 1650 Ti) y ~540 ms solo con CPU, detector + RosaNet,
  ~2,5 rosas por foto. La Orin NX del X2 Ultra debería quedar entre los dos.
- **Detector en las fotos de la finca:** encuentra el **78 %** de las rosas marcadas por la finca.
  Tiene falsos positivos (postes, hojas, una mano); casi siempre salen como `1_inmaduro` o
  `incierta`, así que inflan el conteo de inmaduras pero rara vez dan un falso "listas para cortar".
- **RosaNet (validación cruzada con 64 rosas de la finca):** 75 % de exactitud. Reconoce el 59 % de
  las óptimas. Marca como óptimas 7 de 45 inmaduras (el error más costoso: cortar en punto 2).
  `3_pasado` **no funciona** (la finca dio solo 2 ejemplos).

## Límites que el robot debe tener en cuenta
- **Todo se entrenó con fotos de día.** De noche, con la luz del robot, no está medido: hay que
  tomar fotos de prueba de noche y medir con `ml.evaluate`.
- **Simulación:** las rosas de MuJoCo (figuras) no se parecen a fotos reales; el modelo solo tiene
  sentido con fotos o carteles de rosas reales.
- Si se reentrena la red, los nuevos pesos se copian a `modelos/` con el mismo nombre; el contrato
  de arriba no cambia.
