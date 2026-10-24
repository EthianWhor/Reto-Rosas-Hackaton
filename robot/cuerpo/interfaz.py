"""Lo que la ronda le pide al cuerpo del robot, igual en simulación y en el robot real.

`sim_backend.py` lo cumple con MuJoCo. `real_backend.py` lo cumplirá con el
SDK AimDK_X2 (sección 14 del plan; hoy es un esqueleto). La ronda solo usa estas funciones, así que
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
    rumbo: float = 0.0                    # hacia dónde mira el cuerpo del robot (rad; 0 = +x, π = −x)

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
    def rumbo(self) -> float:
        """Hacia dónde mira el cuerpo (rad; 0 = +x)."""

    @abstractmethod
    def ir_a(self, x: float, y: float, velocidad: float | None = None) -> None:
        """Gira hacia el punto y camina en línea recta hasta él, mirando hacia donde va.
        `velocidad` (m/s) reemplaza la normal, por ejemplo en un tramo difícil."""

    def caminar_hasta(self, x: float) -> None:
        """Camina por el camino actual (a lo largo de x) hasta x."""
        self.ir_a(x, self.posicion()[1])

    @abstractmethod
    def orientar(self, rumbo: float) -> None:
        """Gira en el lugar hasta mirar hacia `rumbo` (rad; 0 = +x)."""

    @abstractmethod
    def obstaculos_adelante(self, distancia_max: float) -> tuple[float | None, float | None]:
        """(distancia al obstáculo alto más cercano, distancia al obstáculo bajo más cercano) hacia
        donde mira el robot, dentro del ancho del camino; None si no hay hasta `distancia_max`.
        Alto = más de `recorrido.alto_obstaculo_m` (frena); bajo = mangueras, desniveles (va despacio).
        En el robot real sale del LiDAR o de la cámara de profundidad."""

    @abstractmethod
    def esperar(self, segundos: float) -> None:
        """Se queda quieto (por ejemplo, esperando a que quiten un obstáculo)."""

    @abstractmethod
    def posar(self, angulos: dict) -> dict:
        """Mueve cintura y cabeza (claves: waist_yaw, waist_pitch, head_yaw, head_pitch) y espera
        a que lleguen. Devuelve los ángulos reales alcanzados."""

    @abstractmethod
    def senalar(self, punto: tuple[float, float, float], segundos: float) -> bool:
        """Acción física: apunta la cabeza (con la cintura) a `punto` (x, y, z del mundo) y prende el
        puntero `segundos`, para que el operario vea qué rosa cortar. Devuelve True si quedó
        apuntando; False si la rosa está fuera del alcance de las articulaciones."""

    @abstractmethod
    def foto(self) -> Captura:
        """Foto RGB (+ profundidad si hay) de la cámara de la cabeza."""

    def nivel_bateria(self) -> float | None:
        """Porcentaje de batería (0–100). None si no se puede leer (en la simulación la batería baja
        se simula con `--parar-despues`)."""
        return None

    def cerrar(self) -> None:
        pass
