"""Arma la escena de MuJoCo: robot + invernadero.

Carga escena_base.xml, le pone al robot la cámara y la linterna de la cabeza,
y agrega las camas con sus rosales según el plano (navegacion/plano.py). El
robot queda parado a la entrada del camino pedido, mirando hacia +x.

También agrega postes, mangueras, desniveles y obstáculos (sim/estructura.py).

Arma dos modelos: el completo (lo que ven la cámara y el sensor) y uno liviano para la
física (robot, piso y camas). Las plantas no se mueven ni chocan, pero MuJoCo calcula su
posición en cada paso: con el invernadero completo (~52.000 piezas) caminar era 10 veces más
lento. El cuerpo simulado camina con el liviano y copia la pose del robot al completo antes de
cada foto o rayo.
"""

import math
import random
from dataclasses import dataclass, field

import mujoco
import numpy as np

from configuracion import ruta
from navegacion.plano import Plano, armar_plano
from sim.estructura import Obstaculo, agregar_estructura
from sim.rosas import RosaVerdad, agregar_rosales

CAMARA = "cam_cabeza"
PUNTERO = "puntero"
# Posición de la cámara en la cabeza y orientación "mirando al frente"
# (las mismas de referencias/jardin_10_plantas.py).
CAMARA_POS = [0.09, -0.014, -0.045]
CAMARA_MAT = [0, 0, -1, -1, 0, 0, 0, 1, 0]
ALTURA_PELVIS = 0.68   # con esta altura los pies quedan apoyados en el piso
ENTRADA_X = -0.6       # el robot arranca antes de que empiecen las camas
COLOR_TIERRA = [0.22, 0.15, 0.09, 1]


@dataclass
class Escena:
    m: mujoco.MjModel        # modelo completo: lo que ven la cámara, el sensor y el visor
    d: mujoco.MjData
    plano: Plano
    verdad: list[RosaVerdad]
    camino: int | None       # None = el robot arrancó en la base
    obstaculos: list[Obstaculo] = field(default_factory=list)
    m_fisica: mujoco.MjModel | None = None   # liviano para caminar (None = el mismo completo)
    d_fisica: mujoco.MjData | None = None


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


def _robot_y_piso(cfg: dict, plano: Plano, inicio: list[float]) -> mujoco.MjSpec:
    """Robot con cámara y luces, la base y las camas: lo que comparten los dos modelos."""
    spec = mujoco.MjSpec.from_file(str(ruta(cfg["sim"]["escena"])))
    ancho, alto = resolucion(cfg)

    cabeza = spec.body("head_pitch_link")
    quat = np.zeros(4)
    mujoco.mju_mat2Quat(quat, np.array(CAMARA_MAT, dtype=float))
    cabeza.add_camera(name=CAMARA, pos=CAMARA_POS, quat=quat,
                      fovy=fovy_grados(cfg["camara"]["fov_h_grados"], ancho, alto))
    cabeza.add_light(name="linterna", pos=[0.07, 0, -0.03], dir=[1, 0, -0.4],
                     diffuse=[0.9, 0.9, 0.8], cutoff=40, exponent=5, castshadow=True)
    # Puntero: foco blanco angosto y fuerte que sale de la cámara; se prende solo al señalar una
    # rosa óptima (verde casi no se ve sobre una rosa roja).
    cabeza.add_light(name=PUNTERO, pos=CAMARA_POS, dir=[1, 0, 0], diffuse=[3.0, 3.0, 3.0],
                     cutoff=4, exponent=1, castshadow=False, active=False)
    spec.body("pelvis").pos = inicio      # el robot y el punto guía arrancan juntos
    spec.body("guia").pos = inicio
    bx, by = cfg["sim"]["base_xy"]   # la base / cargador: una placa en el piso del pasillo principal
    spec.worldbody.add_geom(name="base", type=mujoco.mjtGeom.mjGEOM_BOX, size=[0.3, 0.3, 0.005],
                            pos=[bx, by, 0.005], rgba=[0.15, 0.45, 0.25, 1], contype=0, conaffinity=0)
    _agregar_camas(spec, plano, cfg["sim"]["altura_cama_m"])
    return spec


def _compilar(spec: mujoco.MjSpec) -> tuple[mujoco.MjModel, mujoco.MjData]:
    m = spec.compile()
    d = mujoco.MjData(m)
    mujoco.mj_forward(m, d)
    return m, d


def armar_escena(cfg: dict, camino: int | None = None, en_base: bool = False) -> Escena:
    """Escena con el robot a la entrada de `camino` o, con `en_base`, en la base (`sim.base_xy`)."""
    plano = armar_plano(cfg)
    camino = cfg["sim"]["camino_inicial"] if camino is None else camino
    rng = random.Random(cfg["sim"]["semilla"])
    if en_base:
        inicio = [*cfg["sim"]["base_xy"], ALTURA_PELVIS]
        camino = None
    else:
        inicio = [ENTRADA_X, plano.camino(camino).y, ALTURA_PELVIS]

    spec = _robot_y_piso(cfg, plano, inicio)
    verdad = agregar_rosales(spec, plano, cfg, rng)
    obstaculos = agregar_estructura(spec, plano, cfg)   # postes, mangueras, desniveles, obstáculos
    m, d = _compilar(spec)
    m_fisica, d_fisica = _compilar(_robot_y_piso(cfg, plano, inicio))
    return Escena(m, d, plano, verdad, camino, obstaculos, m_fisica, d_fisica)
