"""Único lugar del robot que toca ml/ (el modelo del equipo, que hace otra persona).

Revisa qué ofrece ml/ en este momento, sin importarlo todavía (así funciona
aunque falte torch), y decide qué usa la ronda cuando el config dice `auto`:

- Hoy en ml/ solo está RosaNet, que clasifica una rosa ya recortada.
- Cuando el equipo termine el detector y se haga `git pull`, basta con que
  existan el módulo y los pesos que dice `modelo_equipo.detector` en el config
  para que el robot lo use solo, en simulación y en el robot real. Si el equipo
  usa otros nombres, solo se cambia el config, no el código.

Los pesos (`runs/.../*.pt`) no se suben a git: después del pull hay que
copiarlos a mano a la ruta del config.
"""

import importlib
import importlib.util

from configuracion import ruta

COMPONENTES = ("clasificador", "detector")
UMBRAL_SEGURO_RESPALDO = 0.6   # el DEFAULT_THRESHOLD de ml/predict.py hoy; solo si no se puede leer


def _existe_modulo(nombre: str) -> bool:
    try:
        return importlib.util.find_spec(nombre) is not None
    except ModuleNotFoundError:  # no existe el paquete padre
        return False


def revisar(cfg: dict) -> dict:
    """Para cada componente del modelo: {"listo": bool, "motivo": str}."""
    estado = {}
    for comp in COMPONENTES:
        c = cfg["modelo_equipo"][comp]
        if not _existe_modulo(c["modulo"]):
            estado[comp] = {"listo": False, "motivo": f"no existe el módulo {c['modulo']} en ml/"}
        elif not ruta(c["pesos"]).exists():
            estado[comp] = {"listo": False, "motivo": f"faltan los pesos {c['pesos']}"}
        elif comp == "clasificador" and not _existe_modulo("torch"):
            estado[comp] = {"listo": False, "motivo": "falta instalar torch"}
        else:
            estado[comp] = {"listo": True, "motivo": f"{c['modulo']}.{c['clase']} con {c['pesos']}"}
    return estado


def elegir(cfg: dict, estado: dict | None = None) -> dict:
    """Resuelve `auto` y revisa que lo pedido se pueda usar.

    Devuelve {"candidatas": ..., "clasificador": ..., "notas": [...]}.
    Si se pide algo a mano (no `auto`) y no está listo, falla con el motivo.
    """
    estado = estado or revisar(cfg)
    modo, rosas = cfg["modo"], cfg["sim"]["rosas"]
    det, clf = estado["detector"], estado["clasificador"]
    det_clasifica = det["listo"] and cfg["modelo_equipo"]["detector"]["clasifica"]
    notas = []

    # En simulación con figuras, el modelo (entrenado con fotos reales) no ve nada.
    solo_oraculo = modo == "sim" and rosas == "figura"

    candidatas = cfg["percepcion"]["candidatas"]
    if candidatas == "auto":
        if solo_oraculo:
            candidatas = "oraculo"
            notas.append("rosas como figuras: se usa el oráculo (con --rosas cartel corre el modelo de verdad)")
        else:
            candidatas = "detector_equipo" if det["listo"] else "color"
            if not det["listo"]:
                notas.append(f"sin detector del equipo ({det['motivo']}): candidatas por máscara roja")

    clasificador = cfg["percepcion"]["clasificador"]
    if clasificador == "auto":
        if solo_oraculo:
            clasificador = "oraculo"
        elif candidatas == "detector_equipo" and det_clasifica:
            clasificador = "detector_equipo"
        elif clf["listo"]:
            clasificador = "rosanet"
        elif modo == "sim":
            clasificador = "oraculo"
            notas.append(f"RosaNet no está lista ({clf['motivo']}): se usa el oráculo")
        else:
            raise RuntimeError(f"modo real sin clasificador: RosaNet no está lista ({clf['motivo']})")

    if modo == "real" and "oraculo" in (candidatas, clasificador):
        raise ValueError("el oráculo solo existe en simulación (usa la verdad de MuJoCo)")
    if "detector_equipo" in (candidatas, clasificador) and not det["listo"]:
        raise RuntimeError(f"se pidió el detector del equipo, pero no está listo: {det['motivo']}")
    if clasificador == "detector_equipo" and not cfg["modelo_equipo"]["detector"]["clasifica"]:
        raise ValueError("el detector del equipo no clasifica (modelo_equipo.detector.clasifica: false)")
    if clasificador == "rosanet" and not clf["listo"]:
        raise RuntimeError(f"se pidió RosaNet, pero no está lista: {clf['motivo']}")

    return {"candidatas": candidatas, "clasificador": clasificador, "notas": notas}


def umbral_seguro(cfg: dict) -> float:
    """Confianza mínima para que una rosa no sea "dudosa". La pone el modelo (DEFAULT_THRESHOLD), no el robot."""
    try:
        modulo = importlib.import_module(cfg["modelo_equipo"]["clasificador"]["modulo"])
        return float(modulo.DEFAULT_THRESHOLD)
    except (ImportError, AttributeError):   # p. ej. sin torch instalado
        return UMBRAL_SEGURO_RESPALDO


def cargar(cfg: dict, componente: str):
    """Importa y crea el componente del equipo: `Clase(pesos)`. Ej.: RosePredictor(runs/rosanet/best.pt)."""
    c = cfg["modelo_equipo"][componente]
    clase = getattr(importlib.import_module(c["modulo"]), c["clase"])
    return clase(ruta(c["pesos"]))
