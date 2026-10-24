"""Análisis de cada foto: candidatas → clase → ubicación (secciones 7 a 9 del plan).

`crear_analizador` arma las piezas que eligió `modelo_equipo.elegir`. Hoy solo
existe el oráculo; los demás modos avisan en qué paso llegan.
"""

import random
from dataclasses import asdict, dataclass

from cuerpo.interfaz import Captura
from navegacion.plano import Plano
from percepcion import modelo_equipo
from percepcion.geometria import ubicar


@dataclass
class Deteccion:
    foto: str
    bbox: list[int]
    clase: str               # inmaduro | optimo | pasado
    confianza: float
    seguro: bool
    probs: dict
    x: float
    y: float
    altura_m: float
    distancia_m: float
    metodo: str              # profundidad | plano
    diametro_cm: float
    cama: int
    lado: str
    metro: float
    tramo: int
    verdad_id: int | None = None   # solo en simulación con oráculo, para medir
    confianza_deteccion: float | None = None   # la del detector del equipo (si lo hubo)

    def a_dict(self) -> dict:
        return asdict(self)


class Analizador:
    def __init__(self, cfg: dict, plano: Plano, candidatas, clasificador):
        self.plano = plano
        self.candidatas = candidatas
        self.clasificador = clasificador
        self.tamano_min = cfg["percepcion"]["tamano_min_px"]
        self.detecciones: list[Deteccion] = []
        self.descartadas = {"pequenas": 0, "sin_ubicacion": 0}

    def analizar(self, cap: Captura, foto: str, camino: int) -> list[Deteccion]:
        cands = []
        for c in self.candidatas.buscar(cap):
            x1, y1, x2, y2 = c.bbox
            if min(x2 - x1, y2 - y1) < self.tamano_min:   # RosaNet no se entrenó con rosas tan pequeñas
                self.descartadas["pequenas"] += 1
            else:
                cands.append(c)
        nuevas = []
        for cand, res in zip(cands, self.clasificador.clasificar(cap, cands)):
            u = ubicar(res["bbox"], cap, self.plano, camino)
            if u is None:
                self.descartadas["sin_ubicacion"] += 1
                continue
            nuevas.append(Deteccion(
                foto=foto, bbox=res["bbox"], clase=res["clase"], confianza=res["confianza"],
                seguro=res["seguro"], probs=res["probs"], x=u.x, y=u.y, altura_m=u.z,
                distancia_m=u.distancia_m, metodo=u.metodo, diametro_cm=u.diametro_cm, cama=u.cama,
                lado=u.lado, metro=u.metro, tramo=u.tramo, verdad_id=cand.verdad_id,
                confianza_deteccion=cand.confianza_deteccion))
        self.detecciones.extend(nuevas)
        return nuevas


def crear_analizador(cfg: dict, eleccion: dict, plano: Plano, verdad=None) -> Analizador:
    from percepcion import candidatas as cands, clasificador as clf

    rng = random.Random(cfg["sim"]["semilla"] + 1)
    eleccion_cand, eleccion_clf = eleccion["candidatas"], eleccion["clasificador"]
    if eleccion_cand == "oraculo":
        candidatas = cands.CandidatasOraculo(verdad, cfg, rng)
    elif eleccion_cand == "detector_equipo":
        candidatas = cands.CandidatasDetector(modelo_equipo.cargar(cfg, "detector"),
                                              cfg["percepcion"].get("detector_tamano_nativo", False))
    elif eleccion_cand == "color":
        candidatas = cands.CandidatasColor()
    else:
        raise ValueError(f"candidatas desconocidas: {eleccion_cand}")

    if eleccion_clf == "oraculo":
        clasificador = clf.ClasificadorOraculo(verdad, cfg, rng, modelo_equipo.umbral_seguro(cfg))
    elif eleccion_clf == "rosanet":
        clasificador = clf.ClasificadorRosaNet(modelo_equipo.cargar(cfg, "clasificador"),
                                               cfg["percepcion"]["margen_recorte"],
                                               cfg["percepcion"].get("fondo_claro"))
    else:
        raise NotImplementedError(f"clasificador '{eleccion_clf}': el detector del equipo no clasifica")
    return Analizador(cfg, plano, candidatas, clasificador)
