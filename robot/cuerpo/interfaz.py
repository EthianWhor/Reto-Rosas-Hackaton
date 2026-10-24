"""Lo que la ronda le pide al cuerpo del robot, igual en simulación y en el robot real.

`sim_backend.py` lo cumple con MuJoCo. `real_backend.py` lo cumplirá con el
SDK AimDK_X2 (sección 14 del plan). La ronda solo usa estas funciones, así que
pasar de simulación a real es cambiar `modo` en el config.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Captura:
    """Una foto con todo lo que hace falta para ubicar después cada rosa en 3D."""
    rgb: np.ndarray                       # alto × ancho × 3, uint8
    profundidad: np.ndarray | None        # alto × ancho, metros (None si la cámara no la da)
    cam_pos: np.ndarray                   # posición de la cámara en el mundo (m)
    cam_mat: np.ndarray                   # 3 × 3, ejes de la cámara en el mundo (convención MuJoCo: mira hacia −z, arriba +y)
    fovy_grados: float
    robot_xy: tuple[float, float]
    angulos: dict = field(default_factory=dict)   # ángulos reales de cintura y cabeza al tomar la foto

    @property
    def ancho(self) -> int:
        return self.rgb.shape[1]

    @property
    def alto(self) -> int:
        return self.rgb.shape[0]

    def intrinsecos(self) -> dict:
        """Focal y centro en píxeles (para pasar de píxel a 3D)."""
        f = (self.alto / 2) / np.tan(np.radians(self.fovy_grados) / 2)
        return {"f": float(f), "cx": self.ancho / 2, "cy": self.alto / 2}


class Cuerpo(ABC):
    @abstractmethod
    def pararse(self) -> None:
        """Deja el robot de pie, quieto, con los brazos pegados al cuerpo."""

    @abstractmethod
    def posicion(self) -> tuple[float, float]:
        """(x, y) del robot en el mundo."""

    @abstractmethod
    def caminar_hasta(self, x: float) -> None:
        """Camina por el camino actual (a lo largo de x) hasta x."""

    @abstractmethod
    def posar(self, angulos: dict) -> dict:
        """Mueve cintura y cabeza (claves: waist_yaw, waist_pitch, head_yaw, head_pitch) y espera
        a que lleguen. Devuelve los ángulos reales alcanzados."""

    @abstractmethod
    def foto(self) -> Captura:
        """Foto RGB (+ profundidad si hay) de la cámara de la cabeza."""

    def cerrar(self) -> None:
        pass
