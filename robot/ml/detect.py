"""Detector de rosas: encuentra dónde hay una rosa en una foto de escena.

Solo ubica rosas (una clase); la categoría de cada una la decide RosaNet
(ml.predict.RosePredictor). Envuelve el YOLO11n ajustado del equipo con los
parámetros medidos en las fotos de la finca.

Uso:
    from ml.detect import RoseDetector
    det = RoseDetector("modelos/detector_rosas.pt")
    for d in det.detect(imagen):          # PIL.Image o np.ndarray RGB
        print(d["bbox"], d["confianza"])  # [x1, y1, x2, y2] en píxeles
"""

from pathlib import Path

import numpy as np
from PIL import Image

DEFAULT_WEIGHTS = Path("modelos/detector_rosas.pt")
# Medido con 30 escenas del invernadero con todas las rosas marcadas (49 rosas, IoU >= 0.5), con el
# detector ajustado con escenas de la finca (entrenado a 960 px): a 960 px y conf 0.25 encuentra el
# 63 % con 5 falsas alarmas; bajar a 0.05 solo sube a 67 % y da 22 falsas alarmas.
DET_CONF, DET_IMGSZ = 0.25, 960
# Con conf baja aparecen cajas enormes sobre el techo del invernadero; una rosa vista
# desde el pasillo nunca ocupa más de unos pocos % de la foto.
MAX_BOX_FRACTION = 0.08
# iou=0.5 (en vez de 0.7 de YOLO): menos cajas duplicadas sobre la misma rosa.
NMS_IOU = 0.5


class RoseDetector:
    def __init__(self, weights: Path | str = DEFAULT_WEIGHTS, conf: float = DET_CONF, imgsz: int = DET_IMGSZ,
                 max_box_fraction: float = MAX_BOX_FRACTION, device: str | None = None):
        from ultralytics import YOLO

        self.model = YOLO(str(weights))
        self.conf, self.imgsz, self.max_box_fraction, self.device = conf, imgsz, max_box_fraction, device

    def detect(self, image: Image.Image | np.ndarray) -> list[dict]:
        """Devuelve [{"bbox": [x1, y1, x2, y2], "confianza": float}] en píxeles de la imagen.

        Un np.ndarray se interpreta como RGB (H, W, 3). Ojo: si viene de OpenCV es BGR;
        convertirlo antes con cv2.cvtColor(img, cv2.COLOR_BGR2RGB).
        """
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        image = image.convert("RGB")
        result = self.model.predict(image, conf=self.conf, imgsz=self.imgsz, iou=NMS_IOU,
                                    device=self.device, verbose=False)[0]
        max_area = self.max_box_fraction * image.width * image.height
        out = []
        for box, score in zip(result.boxes.xyxy.tolist(), result.boxes.conf.tolist()):
            if (box[2] - box[0]) * (box[3] - box[1]) > max_area:
                continue
            out.append({"bbox": box, "confianza": round(score, 3)})
        return out
