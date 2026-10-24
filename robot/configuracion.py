"""Carga config/config.yaml y aplica los cambios que lleguen por la línea de comandos.

La configuración es un dict simple (lo que sale del YAML). Las rutas relativas
se resuelven desde la carpeta robot/, así el programa funciona igual sin
importar desde dónde se llame.
"""

from copy import deepcopy
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent
CONFIG_POR_DEFECTO = RAIZ / "config" / "config.yaml"

OPCIONES = {
    "modo": {"sim", "real"},
    "percepcion.candidatas": {"auto", "oraculo", "color", "detector_equipo"},
    "percepcion.clasificador": {"auto", "oraculo", "rosanet", "detector_equipo"},
    "sim.rosas": {"figura", "cartel"},
}


def cargar(ruta: Path | None = None, cambios: dict | None = None) -> dict:
    """Lee el YAML y aplica `cambios` con claves con punto, por ejemplo {"percepcion.candidatas": "color"}."""
    with open(ruta or CONFIG_POR_DEFECTO, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg = deepcopy(cfg)
    for clave, valor in (cambios or {}).items():
        if valor is not None:
            poner(cfg, clave, valor)
    validar(cfg)
    return cfg


def leer(cfg: dict, clave: str):
    valor = cfg
    for parte in clave.split("."):
        valor = valor[parte]
    return valor


def poner(cfg: dict, clave: str, valor) -> None:
    *camino, ultima = clave.split(".")
    nodo = cfg
    for parte in camino:
        nodo = nodo.setdefault(parte, {})
    nodo[ultima] = valor


def validar(cfg: dict) -> None:
    for clave, permitidas in OPCIONES.items():
        valor = leer(cfg, clave)
        if valor not in permitidas:
            raise ValueError(f"config: {clave} = {valor!r} no es válido. Opciones: {sorted(permitidas)}")


def ruta(valor: str | Path) -> Path:
    """Ruta del config (relativa a robot/) a ruta absoluta."""
    p = Path(valor)
    return p if p.is_absolute() else RAIZ / p
