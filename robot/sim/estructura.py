"""Lo que hay en el invernadero además de los rosales (sección 5.2 y 13.1 del plan).

- Postes cada 3 m en los bordes de las camas y alambres guía: tapan la vista, como en las fotos reales.
- Mangueras cruzando los caminos y desniveles (parches de 1–3 cm): obstáculos bajos (< 5 cm),
  el robot pasa por encima, pero más despacio.
- Obstáculos altos (> 5 cm) en un camino, por ejemplo una caja o un balde: el robot frena y espera.
  Si nadie lo quita, abandona ese camino y lo anota en el reporte. En la simulación un obstáculo
  puede "quitarse solo" después de que el robot espera `se_quita_s` segundos frente a él.

Todo es visual para la física (no empuja al robot, que va sostenido por el punto guía), pero el
sensor de obstáculos del robot (rayos, como un LiDAR) sí lo ve. Usa su propio azar, así que
agregar estructura no cambia las rosas de una semilla.
"""

import random
from dataclasses import dataclass

import mujoco

from navegacion.plano import Plano

GRUPO_ESCENA = 1          # grupo de geoms que ve el sensor (el robot está en los grupos 2 y 3)
COLOR_POSTE = [0.55, 0.55, 0.5, 1]
COLOR_ALAMBRE = [0.7, 0.7, 0.7, 1]
COLOR_MANGUERA = [0.08, 0.2, 0.08, 1]
COLOR_DESNIVEL = [0.28, 0.2, 0.12, 1]
COLOR_OBSTACULO = [0.85, 0.45, 0.1, 1]


@dataclass
class Obstaculo:
    nombre: str              # nombre del geom en MuJoCo
    camino: int
    x: float
    alto_m: float
    se_quita_s: float | None  # None = se queda toda la noche


def _geom(mundo, **kw):
    mundo.add_geom(contype=0, conaffinity=0, group=GRUPO_ESCENA, **kw)


def agregar_estructura(spec: mujoco.MjSpec, plano: Plano, cfg: dict) -> list[Obstaculo]:
    sim = cfg["sim"]
    est = sim.get("estructura") or {}
    rng = random.Random(sim["semilla"] + 7)
    mundo = spec.worldbody.add_body(name="estructura")   # cuerpo fijo sin choques: la física lo salta

    if est.get("postes", True):
        for cama in plano.camas:
            for borde in (cama.y_min + 0.04, cama.y_max - 0.04):
                x = 0.0
                while x <= cama.largo_m + 1e-6:
                    _geom(mundo, name=f"poste_c{cama.numero}_{borde:.2f}_{x:.1f}", type=mujoco.mjtGeom.mjGEOM_CYLINDER,
                          size=[0.025, 1.2, 0], pos=[x, borde, 1.2], rgba=COLOR_POSTE)
                    x += est.get("poste_cada_m", 3.0)
                for altura in (1.2, 1.8):     # alambres guía a lo largo de la cama
                    _geom(mundo, name=f"alambre_c{cama.numero}_{borde:.2f}_{altura}", type=mujoco.mjtGeom.mjGEOM_CAPSULE,
                          size=[0.002, 0, 0], fromto=[0, borde, altura, cama.largo_m, borde, altura], rgba=COLOR_ALAMBRE)

    ancho_camino = cfg["invernadero"]["ancho_camino_m"]
    for camino in plano.caminos:
        for k in range(rng.randint(*est.get("mangueras_por_camino", [1, 2]))):   # cruzan el camino
            x, r = rng.uniform(0.5, plano.largo_m - 0.5), rng.uniform(0.012, 0.02)
            _geom(mundo, name=f"manguera_k{camino.numero}_{k}", type=mujoco.mjtGeom.mjGEOM_CAPSULE, size=[r, 0, 0],
                  fromto=[x, camino.y - ancho_camino / 2 - 0.1, r, x + rng.uniform(-0.15, 0.15),
                          camino.y + ancho_camino / 2 + 0.1, r], rgba=COLOR_MANGUERA)
        for k in range(rng.randint(*est.get("desniveles_por_camino", [0, 2]))):  # parches de 1–3 cm
            alto = rng.uniform(0.01, 0.03)
            _geom(mundo, name=f"desnivel_k{camino.numero}_{k}", type=mujoco.mjtGeom.mjGEOM_BOX,
                  size=[rng.uniform(0.2, 0.4), ancho_camino / 2 - 0.02, alto / 2],
                  pos=[rng.uniform(0.5, plano.largo_m - 0.5), camino.y, alto / 2], rgba=COLOR_DESNIVEL)

    obstaculos = []
    for i, o in enumerate(sim.get("obstaculos") or []):
        if o["camino"] >= len(plano.caminos) or not 0 <= o["x"] <= plano.largo_m:
            continue   # el config es para la escena de prueba; en una más chica puede no caber
        y = plano.camino(o["camino"]).y
        nombre = f"obstaculo{i}"
        _geom(mundo, name=nombre, type=mujoco.mjtGeom.mjGEOM_BOX, size=[0.2, 0.2, o["alto_m"] / 2],
              pos=[o["x"], y, o["alto_m"] / 2], rgba=COLOR_OBSTACULO)
        obstaculos.append(Obstaculo(nombre, o["camino"], o["x"], o["alto_m"], o.get("se_quita_s")))
    return obstaculos
