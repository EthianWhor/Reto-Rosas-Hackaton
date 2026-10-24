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
# Umbral medido para cada detector, a 960 px, con 30 escenas del invernadero con todas las rosas
# marcadas (49 rosas, IoU >= 0.5), de día y en versión "de noche" simulada (data.night_scene):
CONF_BY_MODEL = {
    # Noche (por defecto, el robot hace la ronda de noche): de noche encuentra 55 % con 7 falsas
    # alarmas; de día 47 % con 3. Con umbral más bajo da muchas falsas alarmas (0.25: 32 de noche).
    "detector_rosas.pt": 0.55,
    # Día: de día 63 % con 5 falsas alarmas; de noche solo 22 % con 2.
    "detector_rosas_dia.pt": 0.25,
}
DET_CONF, DET_IMGSZ = CONF_BY_MODEL["detector_rosas.pt"], 960


def default_conf(weights: Path | str) -> float:
    """Umbral recomendado para un archivo de pesos (0.25 si no se midió)."""
    return CONF_BY_MODEL.get(Path(weights).name, 0.25)
# Con conf baja aparecen cajas enormes sobre el techo del invernadero; una rosa vista
# desde el pasillo nunca ocupa más de unos pocos % de la foto.
MAX_BOX_FRACTION = 0.08
# iou=0.5 (en vez de 0.7 de YOLO): menos cajas duplicadas sobre la misma rosa.
NMS_IOU = 0.5


class RoseDetector:
    def __init__(self, weights: Path | str = DEFAULT_WEIGHTS, conf: float | None = None, imgsz: int = DET_IMGSZ,
                 max_box_fraction: float = MAX_BOX_FRACTION, device: str | None = None):
        """conf=None usa el umbral medido para ese archivo de pesos (CONF_BY_MODEL)."""
        from ultralytics import YOLO

        self.model = YOLO(str(weights))
        self.conf = default_conf(weights) if conf is None else conf
        self.imgsz, self.max_box_fraction, self.device = imgsz, max_box_fraction, device

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
