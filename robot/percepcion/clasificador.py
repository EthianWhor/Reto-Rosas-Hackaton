"""Paso 2 de la percepción: decir el estado de cada rosa candidata (sección 7.3).

Todas las versiones devuelven el mismo contrato, por candidata:

    {"bbox": [x1, y1, x2, y2], "clase": "optimo", "confianza": 0.87, "seguro": True,
     "probs": {"inmaduro": 0.10, "optimo": 0.87, "pasado": 0.03}}

Por ahora solo está el oráculo. El adaptador a RosaNet (recorte con 10 % de
margen → RosePredictor) se agrega en el paso de carteles + RosaNet.
"""

import random

from percepcion.candidatas import Candidata
from sim.rosas import RosaVerdad

CLASES = ["inmaduro", "optimo", "pasado"]
VECINAS = {"inmaduro": ["optimo"], "optimo": ["inmaduro", "pasado"], "pasado": ["optimo"]}


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
