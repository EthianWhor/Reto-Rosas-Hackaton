"""Paso 2 de la percepción: decir el estado de cada rosa candidata (sección 7.3).

Todas las versiones devuelven el mismo contrato, por candidata:

    {"bbox": [x1, y1, x2, y2], "clase": "optimo", "confianza": 0.87, "seguro": True,
     "probs": {"inmaduro": 0.10, "optimo": 0.87, "pasado": 0.03}}

- ClasificadorRosaNet: RosaNet del equipo (contrato en robot/CLAUDE.md).
- ClasificadorOraculo: la verdad de MuJoCo con errores a propósito (solo simulación).
"""

import random

import numpy as np
from PIL import Image

from percepcion.candidatas import Candidata
from percepcion.geometria import profundidad_caja
from sim.rosas import RosaVerdad

CLASES = ["inmaduro", "optimo", "pasado"]
VECINAS = {"inmaduro": ["optimo"], "optimo": ["inmaduro", "pasado"], "pasado": ["optimo"]}


def clase_robot(etapa: str) -> str:
    """Etapa de RosaNet → clase del robot: "2_optimo" → "optimo"."""
    return etapa.split("_", 1)[1]


def aclarar_fondo(rgb: np.ndarray, prof: np.ndarray | None, bbox, caja_recorte, color, mas_lejos_m: float) -> np.ndarray:
    """Recorte RGB con el fondo pintado de un color claro, como el de día.

    Fondo = píxeles sin dato de profundidad o más de `mas_lejos_m` detrás de la
    rosa. La rosa y lo que está a su misma distancia o delante (hojas, tallos)
    no se tocan. Sin profundidad, el recorte queda igual.

    Por qué (medido, plan sección 7.7): RosaNet se entrenó con fotos de día con
    fondo claro. Con el margen del recorte negro, como de noche, llama "óptimo"
    a 14–33 de 47 inmaduras; con ese margen gris claro, a 3 de 47, casi como con
    la foto original (2 de 47), sin perder óptimas.
    """
    x1, y1, x2, y2 = caja_recorte
    recorte = rgb[y1:y2, x1:x2].copy()
    if prof is None:
        return recorte
    z_rosa = profundidad_caja(prof, bbox)
    if z_rosa is None:
        return recorte
    p = prof[y1:y2, x1:x2]
    recorte[(p <= 0) | (p > z_rosa + mas_lejos_m)] = color
    return recorte


class ClasificadorRosaNet:
    """Recorta cada rosa como se calibró RosaNet y le pregunta su categoría.

    El recorte usa `pad_box` del equipo (ml/prepare_data.py) con
    `percepcion.margen_recorte` (0,15, el margen de la calibración). Si
    `percepcion.fondo_claro` está activo, antes se aclara el fondo con la
    profundidad (`aclarar_fondo`). Esto cambia lo que recibe la red: hay que
    tenerlo presente al comparar con las métricas del equipo del modelo.
    """

    def __init__(self, predictor, margen: float, fondo: dict | None = None):
        from ml.prepare_data import pad_box
        self.predictor = predictor      # ml.predict.RosePredictor (lo crea modelo_equipo.cargar)
        self.pad_box = pad_box
        self.margen = margen
        self.fondo = fondo if fondo and fondo.get("activo") else None

    def clasificar(self, cap, candidatas: list[Candidata]) -> list[dict]:
        alto, ancho = cap.rgb.shape[:2]
        salida = []
        for cand in candidatas:
            caja = self.pad_box([int(v) for v in cand.bbox], ancho, alto, self.margen)
            if self.fondo is not None:
                pixeles = aclarar_fondo(cap.rgb, cap.profundidad, cand.bbox, caja,
                                        self.fondo["color"], self.fondo["mas_lejos_m"])
            else:
                x1, y1, x2, y2 = caja
                pixeles = cap.rgb[y1:y2, x1:x2]
            r = self.predictor.predict(Image.fromarray(pixeles))
            salida.append({
                "bbox": list(cand.bbox),
                "clase": clase_robot(r["etapa"]),
                "confianza": r["confianza"],
                "seguro": r["seguro"],
                "probs": {clase_robot(k): v for k, v in r["probabilidades"].items()},
                "tips": r.get("tips", {}),
            })
        return salida


class ClasificadorOraculo:
    """Usa la verdad de MuJoCo, con errores a propósito (`oraculo.errores_clase`) y confianzas inventadas.

    Las "lista mañana" (inmaduras avanzadas) reciben una probabilidad de óptimo
    más alta, como haría un modelo que las ve casi listas.
    """

    def __init__(self, verdad: list[RosaVerdad], cfg: dict, rng: random.Random, umbral_seguro: float):
        self.verdad = {r.id: r for r in verdad}
        self.cfg = cfg
        self.rng = rng
        self.umbral = umbral_seguro

    def _probs(self, ganadora: str, conf: float, real: RosaVerdad) -> dict:
        resto = 1 - conf
        otras = [c for c in CLASES if c != ganadora]
        if real.lista_manana and ganadora == "inmaduro":
            preferida, parte = "optimo", 0.9
        else:
            preferida, parte = VECINAS[ganadora][0], 0.7
        probs = {ganadora: conf}
        for c in otras:
            probs[c] = resto * (parte if c == preferida else 1 - parte)
        return {c: round(probs[c], 3) for c in CLASES}

    def clasificar(self, cap, candidatas: list[Candidata]) -> list[dict]:
        o = self.cfg["oraculo"]
        salida = []
        for cand in candidatas:
            real = self.verdad[cand.verdad_id]
            clase = real.estado
            if self.rng.random() < o["errores_clase"]:
                clase = self.rng.choice(VECINAS[clase])
            conf = round(self.rng.uniform(*o["confianza"]), 3)
            if real.lista_manana and clase == "inmaduro":
                conf = round(self.rng.uniform(0.50, 0.70), 3)   # a punto de abrir: el modelo duda más
            salida.append({
                "bbox": list(cand.bbox),
                "clase": clase,
                "confianza": conf,
                "seguro": conf >= self.umbral,
                "probs": self._probs(clase, conf, real),
            })
        return salida
