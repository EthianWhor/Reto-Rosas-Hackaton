"""Píxel → 3D → cama, metro y altura (sección 9 del plan).

Convención de la cámara (la de MuJoCo, la misma que guarda cada Captura):
en ejes de la cámara, x va a la derecha, y hacia arriba y la cámara mira
hacia −z. La profundidad es "plana": la distancia a lo largo del eje de la
cámara, no la distancia en línea recta.

    X = (u − cx) · Z / f      Y = −(v − cy) · Z / f      punto_cámara = (X, Y, −Z)
    punto_mundo = cam_pos + cam_mat · punto_cámara

Sin profundidad (plan B), se lanza el rayo por el píxel y se corta con el
plano vertical del centro de la cama que hay a ese lado del camino.
"""

import math
from dataclasses import dataclass

import numpy as np

from cuerpo.interfaz import Captura
from navegacion.plano import Plano, tramo

TOLERANCIA_CAMA_M = 0.15   # una rosa puede asomarse un poco fuera de su cama


@dataclass
class Ubicacion:
    x: float
    y: float
    z: float                 # altura (m)
    distancia_m: float       # profundidad plana desde la cámara
    metodo: str              # profundidad | plano
    diametro_cm: float
    cama: int
    lado: str                # izq | der (de qué lado del robot estaba la cama)
    metro: float             # metro a lo largo de la cama
    tramo: int


def proyectar(p_mundo, cap: Captura) -> tuple[float, float, float]:
    """(u, v, Z) de un punto del mundo en la foto. Z ≤ 0 = detrás de la cámara."""
    k = cap.intrinsecos()
    p = cap.cam_mat.T @ (np.asarray(p_mundo, dtype=float) - cap.cam_pos)
    z = -p[2]
    if z <= 1e-6:
        return math.nan, math.nan, z
    return k["cx"] + k["f"] * p[0] / z, k["cy"] - k["f"] * p[1] / z, z


def punto_desde_pixel(u: float, v: float, z: float, cap: Captura) -> np.ndarray:
    k = cap.intrinsecos()
    p_cam = np.array([(u - k["cx"]) * z / k["f"], -(v - k["cy"]) * z / k["f"], -z])
    return cap.cam_pos + cap.cam_mat @ p_cam


def profundidad_caja(prof: np.ndarray | None, bbox) -> float | None:
    """Mediana de la profundidad en el centro de la caja (40 % del medio), sin contar los ceros (sin dato)."""
    if prof is None:
        return None
    x1, y1, x2, y2 = bbox
    w, h = x2 - x1, y2 - y1
    cx1, cx2 = int(x1 + 0.3 * w), int(math.ceil(x2 - 0.3 * w))
    cy1, cy2 = int(y1 + 0.3 * h), int(math.ceil(y2 - 0.3 * h))
    zona = prof[max(cy1, 0):max(cy2, cy1 + 1), max(cx1, 0):max(cx2, cx1 + 1)]
    validos = zona[zona > 0]
    return float(np.median(validos)) if validos.size else None


def _corte_con_cama(u, v, cap: Captura, plano: Plano, camino: int) -> tuple[np.ndarray, float] | None:
    """Plan B: corta el rayo del píxel con el plano y = centro de la cama de ese lado."""
    lejos = punto_desde_pixel(u, v, 1.0, cap)          # punto del rayo a Z = 1 m
    direccion = lejos - cap.cam_pos
    c = plano.camino(camino)
    numero = c.cama_izq if direccion[1] > 0 else c.cama_der
    if numero is None or abs(direccion[1]) < 1e-6:
        return None
    t = (plano.cama(numero).y_centro - cap.cam_pos[1]) / direccion[1]   # t = Z en metros
    if t <= 0:
        return None
    return cap.cam_pos + t * direccion, t


def asignar_cama(x: float, y: float, plano: Plano, camino: int) -> tuple[int, str, float, int] | None:
    """(cama, lado, metro, tramo) de un punto, o None si no cae en ninguna cama."""
    cama = next((c for c in plano.camas if c.y_min - TOLERANCIA_CAMA_M <= y <= c.y_max + TOLERANCIA_CAMA_M), None)
    if cama is None:
        return None
    c = plano.camino(camino)
    lado = "izq" if cama.numero == c.cama_izq else "der" if cama.numero == c.cama_der else "otra"
    metro = min(max(x, 0.0), plano.largo_m)
    n_tramos = math.ceil(plano.largo_m / plano.tramo_m)
    return cama.numero, lado, round(metro, 3), min(tramo(metro, plano.tramo_m), n_tramos)


def ubicar(bbox, cap: Captura, plano: Plano, camino: int) -> Ubicacion | None:
    x1, y1, x2, y2 = bbox
    u, v = (x1 + x2) / 2, (y1 + y2) / 2
    z = profundidad_caja(cap.profundidad, bbox)
    if z is not None:
        punto, metodo = punto_desde_pixel(u, v, z, cap), "profundidad"
    else:
        corte = _corte_con_cama(u, v, cap, plano, camino)
        if corte is None:
            return None
        (punto, z), metodo = corte, "plano"
    cama = asignar_cama(punto[0], punto[1], plano, camino)
    if cama is None:
        return None
    diametro_cm = (x2 - x1) * z / cap.intrinsecos()["f"] * 100
    return Ubicacion(round(float(punto[0]), 4), round(float(punto[1]), 4), round(float(punto[2]), 4),
                     round(z, 3), metodo, round(diametro_cm, 2), *cama)
