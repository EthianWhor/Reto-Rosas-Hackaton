"""Arma la escena de MuJoCo: robot + invernadero.

Carga escena_base.xml, le pone al robot la cámara y la linterna de la cabeza,
y agrega las camas con sus rosales según el plano (navegacion/plano.py). El
robot queda parado a la entrada del camino pedido, mirando hacia +x.

Postes, mangueras, desniveles y marcas AprilTag se agregan en los siguientes
pasos (sección 13.1 del plan).
"""

import math
import random
from dataclasses import dataclass

import mujoco
import numpy as np

from configuracion import ruta
from navegacion.plano import Plano, armar_plano
from sim.rosas import RosaVerdad, agregar_rosales

CAMARA = "cam_cabeza"
# Posición de la cámara en la cabeza y orientación "mirando al frente"
# (las mismas de referencias/jardin_10_plantas.py).
CAMARA_POS = [0.09, -0.014, -0.045]
CAMARA_MAT = [0, 0, -1, -1, 0, 0, 0, 1, 0]
ALTURA_PELVIS = 0.68   # con esta altura los pies quedan apoyados en el piso
ENTRADA_X = -0.6       # el robot arranca antes de que empiecen las camas
COLOR_TIERRA = [0.22, 0.15, 0.09, 1]


@dataclass
class Escena:
    m: mujoco.MjModel
    d: mujoco.MjData
    plano: Plano
    verdad: list[RosaVerdad]
    camino: int | None       # None = el robot arrancó en la base


def fovy_grados(fov_h_grados: float, ancho: int, alto: int) -> float:
    """MuJoCo pide el campo de visión vertical: fovy = 2·atan(tan(fov_h/2)·alto/ancho)."""
    return math.degrees(2 * math.atan(math.tan(math.radians(fov_h_grados) / 2) * alto / ancho))


def resolucion(cfg: dict) -> tuple[int, int]:
    """(ancho, alto) de las fotos: la de simulación en modo sim, la real en modo real."""
    cam = cfg["camara"]
    if cfg["modo"] == "sim":
        return cam["sim_ancho"], cam["sim_alto"]
    return cam["ancho"], cam["alto"]


def _agregar_camas(spec: mujoco.MjSpec, plano: Plano, altura: float) -> None:
    for cama in plano.camas:
        spec.worldbody.add_geom(
            name=f"cama{cama.numero}", type=mujoco.mjtGeom.mjGEOM_BOX,
            size=[cama.largo_m / 2, (cama.y_max - cama.y_min) / 2, altura / 2],
            pos=[cama.largo_m / 2, cama.y_centro, altura / 2], rgba=COLOR_TIERRA)


def armar_escena(cfg: dict, camino: int | None = None, en_base: bool = False) -> Escena:
    """Escena con el robot a la entrada de `camino` o, con `en_base`, en la base (`sim.base_xy`)."""
    spec = mujoco.MjSpec.from_file(str(ruta(cfg["sim"]["escena"])))
    plano = armar_plano(cfg)
    camino = cfg["sim"]["camino_inicial"] if camino is None else camino
    rng = random.Random(cfg["sim"]["semilla"])
    ancho, alto = resolucion(cfg)

    cabeza = spec.body("head_pitch_link")
    quat = np.zeros(4)
    mujoco.mju_mat2Quat(quat, np.array(CAMARA_MAT, dtype=float))
    cabeza.add_camera(name=CAMARA, pos=CAMARA_POS, quat=quat,
                      fovy=fovy_grados(cfg["camara"]["fov_h_grados"], ancho, alto))
    cabeza.add_light(name="linterna", pos=[0.07, 0, -0.03], dir=[1, 0, -0.4],
                     diffuse=[0.9, 0.9, 0.8], cutoff=40, exponent=5, castshadow=True)

    # El robot y el punto guía arrancan juntos a la entrada del camino.
    if en_base:
        inicio = [*cfg["sim"]["base_xy"], ALTURA_PELVIS]
        camino = None
    else:
        inicio = [ENTRADA_X, plano.camino(camino).y, ALTURA_PELVIS]
    spec.body("pelvis").pos = inicio
    spec.body("guia").pos = inicio

    bx, by = cfg["sim"]["base_xy"]   # la base / cargador: una placa en el piso del pasillo principal
    spec.worldbody.add_geom(name="base", type=mujoco.mjtGeom.mjGEOM_BOX, size=[0.3, 0.3, 0.005],
                            pos=[bx, by, 0.005], rgba=[0.15, 0.45, 0.25, 1], contype=0, conaffinity=0)
    _agregar_camas(spec, plano, cfg["sim"]["altura_cama_m"])
    verdad = agregar_rosales(spec, plano, cfg, rng)

    m = spec.compile()
    d = mujoco.MjData(m)
    mujoco.mj_forward(m, d)
    return Escena(m, d, plano, verdad, camino)
