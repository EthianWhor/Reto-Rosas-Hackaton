"""Plano del invernadero: dónde queda cada cama y cada camino (sección 4 del plan).

Ejes del mundo (los mismos de MuJoCo):
- x: a lo largo de las camas. x = 0 es la cabecera (pasillo principal) y
  x = largo es el fondo.
- y: a lo ancho. El camino 0 queda en la orilla (y ≈ 0) y los demás van
  hacia +y, alternando con las camas:

    y ↑   ...
          camino 2
          cama 2
          camino 1      ← el robot camina por aquí: a su izquierda (+y) la cama 2, a su derecha la cama 1
          cama 1
          camino 0
    y = 0 ─────────────────────────────► x

El camino k queda entre la cama k (derecha, yendo hacia +x) y la cama k+1
(izquierda). Los caminos de las orillas (0 y N) solo ven una cama.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Cama:
    numero: int        # 1..N
    y_min: float
    y_max: float
    largo_m: float

    @property
    def y_centro(self) -> float:
        return (self.y_min + self.y_max) / 2


@dataclass(frozen=True)
class Camino:
    numero: int        # 0..N
    y: float           # centro del camino
    cama_der: int | None   # cama a la derecha yendo hacia +x
    cama_izq: int | None   # cama a la izquierda yendo hacia +x


@dataclass(frozen=True)
class Plano:
    camas: list[Cama]
    caminos: list[Camino]
    largo_m: float
    tramo_m: float

    def camino(self, numero: int) -> Camino:
        return self.caminos[numero]

    def cama(self, numero: int) -> Cama:
        return self.camas[numero - 1]


def armar_plano(cfg: dict) -> Plano:
    """Plano con las medidas de `invernadero`; en simulación, `sim.camas` y `sim.largo_cama_m` lo achican."""
    inv = cfg["invernadero"]
    n_camas, largo = inv["camas"], inv["largo_cama_m"]
    if cfg["modo"] == "sim":
        n_camas = cfg["sim"].get("camas") or n_camas
        largo = cfg["sim"].get("largo_cama_m") or largo
    ancho_cama, ancho_camino = inv["ancho_cama_m"], inv["ancho_camino_m"]
    paso = ancho_cama + ancho_camino

    camas = [Cama(c, (c - 1) * paso + ancho_camino, (c - 1) * paso + ancho_camino + ancho_cama, largo)
             for c in range(1, n_camas + 1)]
    caminos = [Camino(k, k * paso + ancho_camino / 2,
                      cama_der=k if k >= 1 else None,
                      cama_izq=k + 1 if k < n_camas else None)
               for k in range(n_camas + 1)]
    return Plano(camas, caminos, largo, inv["tramo_m"])


def tramo(metro: float, tramo_m: float) -> int:
    """Tramo (1, 2, …) que corresponde a un metro de la cama: T1 = 0–5 m, T2 = 5–10 m…"""
    return int(metro // tramo_m) + 1
