"""Juntar la misma rosa vista en varias fotos (sección 9.4 del plan).

Si dos detecciones quedan a menos de `dedup.radio_m` en 3D, son la misma rosa.
Se queda la de mejor confianza (y, si empatan, la tomada más cerca); las demás
quedan como "vistas extra".
"""

import math
from dataclasses import asdict, dataclass, field

from percepcion.analisis import Deteccion


@dataclass
class Rosa:
    rosa_id: str             # INV1-C07-T3-12.35-1.84 (cuadrante + metro + altura)
    cuadrante_id: str        # INV1-C07-T3
    clase: str
    confianza: float
    seguro: bool
    probs: dict
    cama: int
    tramo: int
    lado: str
    metro: float
    altura_m: float
    x: float
    y: float
    diametro_cm: float
    distancia_m: float
    foto: str                # la foto de la mejor vista
    vistas: int = 1
    fotos: list[str] = field(default_factory=list)
    verdad_id: int | None = None

    def a_dict(self) -> dict:
        return asdict(self)


def cuadrante_id(invernadero: str, cama: int, tramo: int) -> str:
    return f"{invernadero}-C{cama:02d}-T{tramo}"


def _distancia(a: Deteccion, b: Deteccion) -> float:
    return math.dist((a.x, a.y, a.altura_m), (b.x, b.y, b.altura_m))


def juntar(detecciones: list[Deteccion], radio_m: float, invernadero: str) -> list[Rosa]:
    orden = sorted(detecciones, key=lambda d: (-d.confianza, d.distancia_m))
    grupos: list[tuple[Deteccion, list[Deteccion]]] = []   # (mejor vista, todas las vistas)
    for det in orden:
        cerca = [g for g in grupos if _distancia(g[0], det) < radio_m]
        if cerca:
            min(cerca, key=lambda g: _distancia(g[0], det))[1].append(det)
        else:
            grupos.append((det, [det]))

    rosas = []
    for mejor, vistas in grupos:
        cuad = cuadrante_id(invernadero, mejor.cama, mejor.tramo)
        rosas.append(Rosa(
            rosa_id=f"{cuad}-{mejor.metro:.2f}-{mejor.altura_m:.2f}", cuadrante_id=cuad,
            clase=mejor.clase, confianza=mejor.confianza, seguro=mejor.seguro, probs=mejor.probs,
            cama=mejor.cama, tramo=mejor.tramo, lado=mejor.lado, metro=mejor.metro,
            altura_m=mejor.altura_m, x=mejor.x, y=mejor.y, diametro_cm=mejor.diametro_cm,
            distancia_m=mejor.distancia_m, foto=mejor.foto, vistas=len(vistas),
            fotos=[v.foto for v in vistas], verdad_id=mejor.verdad_id))
    return sorted(rosas, key=lambda r: (r.cama, r.metro, r.altura_m))
