"""Por dónde va el robot: ruta en serpiente y paradas de cada camino (sección 4.3 y 4.4 del plan).

    pasillo principal (cabecera, x < 0)          pasillo del fondo (x > largo)
    [base] ─► camino 0 ──────────────────────────► ┐
              camino 1 ◄────────────────────────── ┘
           ┌─────────────────────────────────────
           └► camino 2 ──────────────────────────► ...

Entra por un camino, lo recorre entero, sale por el otro extremo, se corre al
siguiente camino por el pasillo y vuelve en sentido contrario. Así no repite
caminos y nunca da la vuelta dentro de un camino angosto. Al final vuelve a
la base.
"""

import math
from dataclasses import dataclass

from navegacion.plano import Plano

SALIDA_M = 0.6   # cuánto se aleja de la punta de la cama al entrar o salir de un camino


@dataclass(frozen=True)
class Tramo:
    """Un camino recorrido en un sentido (+1 = hacia el fondo, −1 = hacia la cabecera)."""
    camino: int
    sentido: int
    y: float
    xs: tuple[float, ...]     # paradas en el orden en que las visita
    entrada_x: float
    salida_x: float

    @property
    def rumbo(self) -> float:
        return 0.0 if self.sentido > 0 else math.pi


def paradas(plano: Plano, cfg: dict) -> list[float]:
    """x de cada parada, de la cabecera al fondo: 0, paso, 2·paso, … y siempre una al final de la cama."""
    paso = cfg["recorrido"]["paso_entre_paradas_m"]
    xs, x = [], 0.0
    while x < plano.largo_m - 1e-6:
        xs.append(round(x, 3))
        x += paso
    xs.append(plano.largo_m)
    return xs


def numero_parada(plano: Plano, cfg: dict, x: float) -> int:
    """Número de una parada contando desde la cabecera, igual en los dos sentidos (para nombrar las fotos)."""
    xs = paradas(plano, cfg)
    return min(range(len(xs)), key=lambda k: abs(xs[k] - x))


def serpiente(plano: Plano, cfg: dict, caminos: list[int], desde_cabecera: bool = True) -> list[Tramo]:
    """Tramos en orden: el primero se aleja del lado donde está el robot, el siguiente vuelve, y así.

    `desde_cabecera=False` sirve cuando el robot quedó en el pasillo del fondo (por ejemplo, después
    de abandonar un camino bloqueado y volver a planear).
    """
    xs = paradas(plano, cfg)
    cabecera, fondo = -SALIDA_M, plano.largo_m + SALIDA_M
    tramos = []
    for i, numero in enumerate(caminos):
        sentido = (1 if i % 2 == 0 else -1) * (1 if desde_cabecera else -1)
        tramos.append(Tramo(
            camino=numero, sentido=sentido, y=plano.camino(numero).y,
            xs=tuple(xs if sentido > 0 else reversed(xs)),
            entrada_x=cabecera if sentido > 0 else fondo,
            salida_x=fondo if sentido > 0 else cabecera))
    return tramos


def camino_a_la_base(plano: Plano, desde: tuple[float, float], base: tuple[float, float]) -> list[tuple[float, float]]:
    """Puntos para volver a la base sin atravesar camas.

    La base está en el pasillo principal (cabecera). Si el robot quedó en el
    pasillo del fondo, primero vuelve por el último camino (sin tomar fotos).
    """
    x, y = desde
    puntos = []
    if x > plano.largo_m:                       # está en el pasillo del fondo
        puntos.append((-SALIDA_M, y))           # vuelve por el mismo camino hasta la cabecera
    puntos.append(base)
    return puntos
