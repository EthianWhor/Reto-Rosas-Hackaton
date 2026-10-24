"""Paso 1 de la percepción: encontrar las rosas en la foto y dar una caja por rosa (sección 7.2).

Tres formas, todas con `buscar(captura) -> list[Candidata]`:
- CandidatasDetector: el detector del equipo (ml.detect.RoseDetector, YOLO11n). Es la de verdad.
- CandidatasColor: máscara de rojo. Respaldo si el detector no está instalado.
- CandidatasOraculo: la verdad de MuJoCo (solo simulación, con rosas como figuras).

Las fotos del robot (MuJoCo y la cámara real a través de su driver) llegan en
RGB. Si algún día se leen con OpenCV (BGR), hay que pasarlas a RGB antes del
detector: cv2.cvtColor(img, cv2.COLOR_BGR2RGB).
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
    confianza_deteccion: float | None = None


class CandidatasDetector:
    """El detector del equipo. Solo ubica; la categoría la da RosaNet (robot/CLAUDE.md).

    Con `tamano_nativo`, el detector mira la foto sin achicarla: usa el tamaño de la foto si es mayor
    que el suyo (`imgsz`, 960 px). Las rosas de la ronda se ven pequeñas y al achicar la foto de
    1920 px a 960 quedaban sin detectar (en la simulación, cobertura 50 % → 71 %; plan, sección 7.11).
    Una foto más chica (la webcam del modo foto) sigue igual que antes.
    """

    def __init__(self, detector, tamano_nativo: bool = False):
        self.detector = detector   # ml.detect.RoseDetector (lo crea modelo_equipo.cargar)
        self.tamano_equipo = getattr(detector, "imgsz", None) if tamano_nativo else None

    def buscar(self, cap: Captura) -> list[Candidata]:
        if self.tamano_equipo:     # múltiplo de 32, como pide YOLO
            self.detector.imgsz = max(self.tamano_equipo, -(-max(cap.ancho, cap.alto) // 32) * 32)
        salida = []
        for d in self.detector.detect(cap.rgb):           # cap.rgb ya es RGB
            x1, y1, x2, y2 = (round(v) for v in d["bbox"])
            salida.append(Candidata((x1, y1, x2, y2), confianza_deteccion=d["confianza"]))
        return salida


class CandidatasColor:
    """Respaldo sin el detector: manchas rojas en la foto (sección 7.2 del plan).

    Rojo = tono cerca de 0° o de 180° en HSV, con color y brillo suficientes. Los
    umbrales son para la luz del robot y hay que calibrarlos con fotos de noche.
    Límite conocido: dos rosas pegadas salen como una sola mancha.
    """

    SAT_MIN, BRILLO_MIN, TONO_MAX = 90, 40, 12   # OpenCV: tono de 0 a 180

    def buscar(self, cap: Captura) -> list[Candidata]:
        import cv2
        hsv = cv2.cvtColor(cap.rgb, cv2.COLOR_RGB2HSV)
        h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
        rojo = ((h <= self.TONO_MAX) | (h >= 180 - self.TONO_MAX)) & (s >= self.SAT_MIN) & (v >= self.BRILLO_MIN)
        mascara = cv2.morphologyEx(rojo.astype(np.uint8) * 255, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        n, _, stats, _ = cv2.connectedComponentsWithStats(mascara)
        salida = []
        for x, y, w, hh, area in stats[1:n]:
            if area < 30 or not (0.3 <= w / max(hh, 1) <= 3.0):
                continue
            salida.append(Candidata((int(x), int(y), int(x + w), int(y + hh))))
        return salida


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
