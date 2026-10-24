"""Rosales de la simulación: tallos, hojas y la cabeza de cada rosa según su estado.

Cada rosa guarda su verdad (estado, posición de la cabeza, diámetro) para el
oráculo y para medir aciertos. Las formas y colores salen de la tabla de la
sección 13.2 del plan. Todo es visual (no choca con el robot), como las hojas
reales, que son flexibles.

Dos formas de dibujar la cabeza (`sim.rosas`): figura (formas simples, para el
oráculo) o cartel (una foto real de una rosa de la finca, para que el detector
y RosaNet del equipo la vean; sección 7.4).
"""

import math
import random
from dataclasses import asdict, dataclass

import mujoco
import numpy as np

from navegacion.plano import Plano

VERDE_TALLO = [0.10, 0.30, 0.08, 1]
VERDE_HOJA = [0.12, 0.38, 0.10, 1]
VERDE_SEPALO = [0.15, 0.42, 0.12, 1]

# estado de la figura: (rango de diámetro en cm, color RGB de los pétalos)
FIGURAS = {
    "inmaduro": ((3.0, 4.0), (0.40, 0.02, 0.05)),
    "lista_manana": ((4.0, 4.8), (0.55, 0.03, 0.06)),
    "optimo": ((4.8, 5.5), (0.75, 0.04, 0.08)),
    "pasado": ((6.0, 8.0), (0.60, 0.05, 0.07)),
}
BORDE_PASADO = (0.25, 0.02, 0.03)
CENTRO_OPTIMO = (0.45, 0.02, 0.05)


@dataclass
class RosaVerdad:
    id: int
    estado: str            # inmaduro | optimo | pasado (las 3 clases de RosaNet)
    lista_manana: bool     # solo puede ser True si estado == inmaduro
    cama: int
    x: float               # centro de la cabeza, en el mundo
    y: float
    z: float
    diametro_cm: float

    def a_dict(self) -> dict:
        return asdict(self)


def _color(base, rng: random.Random, var: float = 0.08) -> list[float]:
    return [min(1.0, max(0.0, c * rng.uniform(1 - var, 1 + var))) for c in base] + [1]


def _sorteo_estado(prob: dict, rng: random.Random) -> str:
    return rng.choices(list(prob), weights=list(prob.values()))[0]


def _geom(cuerpo, nombre, tipo, size, pos, rgba, euler=(0, 0, 0)):
    cuerpo.add_geom(name=nombre, type=tipo, size=size, pos=pos, euler=list(euler), rgba=rgba,
                    contype=0, conaffinity=0, group=1)


def _sepalos(mundo, nombre, cx, cy, cz, r, inclinacion, rng):
    """3 sépalos alrededor de la base de la cabeza. inclinacion: 0 = pegados, ~2,2 = hacia abajo."""
    for k in range(3):
        a = 2 * math.pi * k / 3 + rng.uniform(-0.3, 0.3)
        largo = 1.1 * r
        # el sépalo sale de la base de la cabeza y se abre `inclinacion` radianes hacia afuera
        dx = math.cos(a) * math.sin(inclinacion) * largo
        dy = math.sin(a) * math.sin(inclinacion) * largo
        dz = math.cos(inclinacion) * largo
        base = (cx + 0.8 * r * math.cos(a), cy + 0.8 * r * math.sin(a), cz - 0.5 * r)
        mundo.add_geom(name=f"{nombre}_sepalo{k}", type=mujoco.mjtGeom.mjGEOM_CAPSULE, size=[0.002, 0, 0],
                       fromto=[*base, base[0] + dx, base[1] + dy, base[2] + dz],
                       rgba=VERDE_SEPALO, contype=0, conaffinity=0, group=1)


def _cabeza(mundo, nombre, figura, cx, cy, cz, d_cm, rng):
    r = d_cm / 200  # radio en metros
    color = _color(FIGURAS[figura][1], rng)
    elip, cil, esf = mujoco.mjtGeom.mjGEOM_ELLIPSOID, mujoco.mjtGeom.mjGEOM_CYLINDER, mujoco.mjtGeom.mjGEOM_SPHERE
    if figura == "inmaduro":           # bala alargada, sépalos pegados
        _geom(mundo, nombre, elip, [r, r, 1.6 * r], [cx, cy, cz], color)
        _sepalos(mundo, nombre, cx, cy, cz, r, 0.15, rng)
    elif figura == "lista_manana":     # un poco más ancha, sépalos medio abiertos
        _geom(mundo, nombre, elip, [r, r, 1.3 * r], [cx, cy, cz], color)
        _sepalos(mundo, nombre, cx, cy, cz, r, 0.8, rng)
    elif figura == "optimo":           # copa: base angosta + borde ancho arriba + centro visible
        _geom(mundo, nombre, elip, [0.75 * r, 0.75 * r, 0.9 * r], [cx, cy, cz - 0.3 * r], color)
        _geom(mundo, f"{nombre}_copa", cil, [r, 0.25 * r, 0], [cx, cy, cz + 0.35 * r], color)
        _geom(mundo, f"{nombre}_centro", esf, [0.3 * r, 0, 0], [cx, cy, cz + 0.55 * r], _color(CENTRO_OPTIMO, rng))
        _sepalos(mundo, nombre, cx, cy, cz, r, 2.2, rng)
    else:                              # pasado: disco ancho y plano con bordes oscuros
        _geom(mundo, nombre, cil, [r, 0.15 * r, 0], [cx, cy, cz], color)
        _geom(mundo, f"{nombre}_borde", cil, [1.04 * r, 0.08 * r, 0], [cx, cy, cz - 0.1 * r], _color(BORDE_PASADO, rng))
        _sepalos(mundo, nombre, cx, cy, cz, 0.6 * r, 2.4, rng)


def preparar_carteles(spec: mujoco.MjSpec, cfg: dict) -> dict[str, list[tuple[str, float]]]:
    """Carga las fotos reales de rosas como texturas. Devuelve {estado: [(material, alto/ancho), ...]}.

    Las fotos son los recortes de la finca de `sim.carteles_dir` (una carpeta por
    categoría, como en ml/stages.py). MuJoCo solo lee PNG, así que se convierten
    una vez a datos/cache_carteles/.
    """
    from PIL import Image

    from configuracion import ruta
    origen = ruta(cfg["sim"]["carteles_dir"])
    cache = ruta(cfg["datos_dir"]) / "cache_carteles"
    cache.mkdir(parents=True, exist_ok=True)
    carteles: dict[str, list[tuple[str, float]]] = {}
    for carpeta in sorted(p for p in origen.iterdir() if p.is_dir()):
        estado = carpeta.name.split("_", 1)[1]           # "2_optimo" → "optimo"
        for foto in sorted(carpeta.glob("*.jpg")):
            png = cache / f"{carpeta.name}__{foto.stem}.png"
            with Image.open(foto) as im:
                if not png.exists():
                    im.convert("RGB").save(png)
                alto_rel = im.height / im.width
            nombre = f"cartel_{carpeta.name}_{foto.stem}"
            spec.add_texture(name=nombre, type=mujoco.mjtTexture.mjTEXTURE_2D, file=str(png))
            mat = spec.add_material(name=nombre, emission=0.25, specular=0.0)
            mat.textures[mujoco.mjtTextureRole.mjTEXROLE_RGB] = nombre
            carteles.setdefault(estado, []).append((nombre, alto_rel))
    return carteles


# Rotación inicial de un plano para que mire hacia −y o hacia +y, con la foto derecha.
_QUAT_MIRA = {}
for _signo in (-1, 1):
    _q = np.zeros(4)
    mujoco.mju_mat2Quat(_q, np.array([[-_signo, 0, 0], [0, 0, _signo], [0, 1, 0]], dtype=float).ravel())
    _QUAT_MIRA[_signo] = _q.tolist()


SUFIJO_CARTEL = "_cartel"


def _cartel(mundo, nombre, material, alto_rel, cx, cy, cz, d_cm):
    """Un plano con la foto de la rosa. Antes de cada foto gira para mirar a la cámara
    (`mirar_a_la_camara`): una rosa real es 3D y se ve bien desde cualquier lado; una foto plana
    vista de lado se deforma y RosaNet no la reconoce."""
    medio_ancho = d_cm / 200 * 1.3   # la foto trae algo de margen alrededor de la rosa
    mundo.add_geom(name=f"{nombre}{SUFIJO_CARTEL}", type=mujoco.mjtGeom.mjGEOM_PLANE,
                   size=[medio_ancho, medio_ancho * alto_rel, 0.01], pos=[cx, cy, cz],
                   quat=_QUAT_MIRA[-1], material=material, contype=0, conaffinity=0, group=1)


def ids_carteles(m: mujoco.MjModel) -> np.ndarray:
    return np.array([g for g in range(m.ngeom) if (m.geom(g).name or "").endswith(SUFIJO_CARTEL)], dtype=int)


def mirar_a_la_camara(m: mujoco.MjModel, d: mujoco.MjData, ids: np.ndarray, cam_pos: np.ndarray) -> None:
    """Gira cada cartel para que su cara (eje z del plano) apunte a la cámara, con la foto derecha."""
    if ids.size == 0:
        return
    centros = m.geom_pos[ids]
    z = cam_pos - centros
    z /= np.linalg.norm(z, axis=1, keepdims=True)
    arriba = np.array([0.0, 0.0, 1.0])
    x = np.cross(arriba, z)
    x /= np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-9)
    y = np.cross(z, x)
    for k, g in enumerate(ids):
        mat = np.column_stack([x[k], y[k], z[k]])
        mujoco.mju_mat2Quat(m.geom_quat[g], mat.ravel())
    mujoco.mj_kinematics(m, d)


def agregar_rosales(spec: mujoco.MjSpec, plano: Plano, cfg: dict, rng: random.Random) -> list[RosaVerdad]:
    """Siembra rosales en todas las camas del plano y devuelve la verdad de cada rosa.

    Con `sim.rosas: figura` la cabeza es una figura según su estado (para el
    oráculo). Con `sim.rosas: cartel` es una foto real de una rosa de la finca
    de esa categoría, para que el detector y RosaNet del equipo la vean.
    """
    sim, rosas_cfg = cfg["sim"], cfg["rosas"]
    mundo = spec.worldbody
    z_suelo = sim["altura_cama_m"]
    margen = 0.12
    verdad = []
    carteles = preparar_carteles(spec, cfg) if sim["rosas"] == "cartel" else None
    prob = dict(sim["prob_estados"])
    if carteles is not None:
        # una foto no puede mostrar "lista mañana": esas cuentan como inmaduras
        prob["inmaduro"] = prob.get("inmaduro", 0) + prob.pop("lista_manana", 0)
        prob = {e: p for e, p in prob.items() if e in carteles}
    for cama in plano.camas:
        for metro in range(int(cama.largo_m)):
            for _ in range(rng.randint(*sim["tallos_por_metro"])):
                i = len(verdad)
                bx = rng.uniform(metro, metro + 1)
                by = rng.uniform(cama.y_min + margen, cama.y_max - margen)
                hz = rng.uniform(rosas_cfg["altura_min_m"], rosas_cfg["altura_max_m"])
                # el tallo se inclina un poco: la cabeza no queda justo encima de la base
                hx, hy = bx + rng.uniform(-0.05, 0.05), by + rng.uniform(-0.05, 0.05)

                figura = _sorteo_estado(prob, rng)
                d_cm = rng.uniform(*FIGURAS[figura][0])
                nombre = f"rosa{i}"
                r = d_cm / 200
                mundo.add_geom(name=f"{nombre}_tallo", type=mujoco.mjtGeom.mjGEOM_CAPSULE, size=[0.004, 0, 0],
                               fromto=[bx, by, z_suelo, hx, hy, hz - 1.5 * r], rgba=VERDE_TALLO,
                               contype=0, conaffinity=0, group=1)
                for k in range(3):  # hojas a lo largo del tallo
                    f = rng.uniform(0.3, 0.85)
                    a = rng.uniform(0, 2 * math.pi)
                    mundo.add_geom(name=f"{nombre}_hoja{k}", type=mujoco.mjtGeom.mjGEOM_ELLIPSOID,
                                   size=[0.035, 0.018, 0.003],
                                   pos=[bx + f * (hx - bx) + 0.03 * math.cos(a),
                                        by + f * (hy - by) + 0.03 * math.sin(a),
                                        z_suelo + f * (hz - z_suelo)],
                                   euler=[0, -0.4, a], rgba=_color(VERDE_HOJA[:3], rng),
                                   contype=0, conaffinity=0, group=1)
                if carteles is None:
                    _cabeza(mundo, f"{nombre}_cabeza", figura, hx, hy, hz, d_cm, rng)
                else:
                    material, alto_rel = rng.choice(carteles[figura])
                    _cartel(mundo, f"{nombre}_cabeza", material, alto_rel, hx, hy, hz, d_cm)

                estado = "inmaduro" if figura == "lista_manana" else figura
                verdad.append(RosaVerdad(i, estado, figura == "lista_manana", cama.numero,
                                         round(hx, 4), round(hy, 4), round(hz, 4), round(d_cm, 2)))
    return verdad
