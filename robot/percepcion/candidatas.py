"""Paso 1 de la percepción: encontrar las rosas en la foto y dar una caja por rosa (sección 7.2).

Por ahora solo está el oráculo (simulación). La máscara roja y el detector del
equipo se agregan en el paso de carteles + RosaNet.
"""

import random
from dataclasses import dataclass

import numpy as np

from cuerpo.interfaz import Captura
from percepcion.geometria import proyectar
from sim.rosas import RosaVerdad

# alto de la caja / ancho, según cómo se ve cada figura (sim/rosas.py)
ALTO_RELATIVO = {"inmaduro": 1.4, "optimo": 1.0, "pasado": 0.6}
VISIBLE_MIN = 0.3          # fracción del centro de la caja que debe verse (si no, está tapada)
TOLERANCIA_PROF_M = 0.04


@dataclass
class Candidata:
    bbox: tuple[int, int, int, int]      # x1, y1, x2, y2 en píxeles de la foto completa
    verdad_id: int | None = None         # solo el oráculo sabe qué rosa es


class CandidatasOraculo:
    """Usa la verdad de MuJoCo: proyecta cada cabeza a la foto y da su caja si se ve.

    "Se ve" = está delante de la cámara, dentro de la foto, a menos de
    `camara.distancia_max_m` y sin algo que la tape (se revisa con la profundidad).
    A propósito, a veces no ve una rosa (`oraculo.fallos`) y mueve un poco las cajas.
    """

    def __init__(self, verdad: list[RosaVerdad], cfg: dict, rng: random.Random):
        self.verdad = verdad
        self.cfg = cfg
        self.rng = rng
        self.dist_max = cfg["camara"]["distancia_max_m"]

    def _visible(self, cap: Captura, bbox, z: float) -> bool:
        if cap.profundidad is None:
            return True
        x1, y1, x2, y2 = bbox
        w, h = x2 - x1, y2 - y1
        zona = cap.profundidad[int(y1 + 0.25 * h):int(y2 - 0.25 * h) + 1, int(x1 + 0.25 * w):int(x2 - 0.25 * w) + 1]
        return zona.size > 0 and np.mean(np.abs(zona - z) < TOLERANCIA_PROF_M) >= VISIBLE_MIN

    def buscar(self, cap: Captura) -> list[Candidata]:
        f = cap.intrinsecos()["f"]
        ruido = self.cfg["oraculo"]["ruido_caja"]
        fallos = self.cfg["oraculo"]["fallos"]
        salida = []
        for r in self.verdad:
            u, v, z = proyectar((r.x, r.y, r.z), cap)
            if not (0.2 < z <= self.dist_max):
                continue
            medio_w = f * (r.diametro_cm / 200) / z
            medio_h = medio_w * ALTO_RELATIVO[r.estado]
            exacta = (u - medio_w, v - medio_h, u + medio_w, v + medio_h)
            if exacta[0] < 0 or exacta[1] < 0 or exacta[2] >= cap.ancho or exacta[3] >= cap.alto:
                continue
            if not self._visible(cap, exacta, z) or self.rng.random() < fallos:
                continue
            # caja con error, como la daría un modelo
            du, dv = (self.rng.uniform(-ruido, ruido) * 2 * medio_w for _ in range(2))
            escala = 1 + self.rng.uniform(-ruido, ruido)
            bbox = (round(u + du - medio_w * escala), round(v + dv - medio_h * escala),
                    round(u + du + medio_w * escala), round(v + dv + medio_h * escala))
            salida.append(Candidata(bbox, r.id))
        return salida
