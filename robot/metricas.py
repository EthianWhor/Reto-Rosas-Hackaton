"""Métricas de la simulación: lo que encontró el robot contra la verdad (sección 16.1 del plan).

Cada rosa encontrada se empareja con la rosa real más cercana a menos de
`RADIO_EMPAREJAR_M`. Se empareja por posición (no por el id del oráculo), así
las mismas métricas sirven cuando se use RosaNet sobre carteles.
"""

import math

from percepcion.dedup import Rosa
from sim.rosas import RosaVerdad

RADIO_EMPAREJAR_M = 0.10


def _media(valores) -> float | None:
    return round(sum(valores) / len(valores), 2) if valores else None


def comparar(rosas: list[Rosa], verdad: list[RosaVerdad], camas: set[int], estados: dict | None = None) -> dict:
    """`estados` (rosa_id → estado final de madurez.py) agrega las métricas de "lista mañana"."""
    reales = [r for r in verdad if r.cama in camas]
    usadas: set[int] = set()
    duplicadas = falsas = 0
    err_altura, err_metro, pares = [], [], []
    for rosa in sorted(rosas, key=lambda r: -r.confianza):
        cerca = min(reales, key=lambda v: math.dist((v.x, v.y, v.z), (rosa.x, rosa.y, rosa.altura_m)), default=None)
        if cerca is None or math.dist((cerca.x, cerca.y, cerca.z), (rosa.x, rosa.y, rosa.altura_m)) > RADIO_EMPAREJAR_M:
            falsas += 1
            continue
        if cerca.id in usadas:
            duplicadas += 1
            continue
        usadas.add(cerca.id)
        pares.append((rosa, cerca))
        err_altura.append(abs(rosa.altura_m - cerca.z) * 100)
        err_metro.append(abs(rosa.x - cerca.x) * 100)

    dice_optimo = [(r, v) for r, v in pares if r.clase == "optimo"]
    reales_optimo = [v for v in reales if v.estado == "optimo"]
    aciertos_optimo = sum(v.estado == "optimo" for _, v in dice_optimo)
    extra = {}
    if estados is not None:
        dice_manana = [v for r, v in pares if estados.get(r.rosa_id) == "lista_manana"]
        vistas_manana = [v for _, v in pares if v.lista_manana]
        extra = {
            "precision_lista_manana": round(sum(v.lista_manana for v in dice_manana) / len(dice_manana), 3)
            if dice_manana else None,
            "recall_lista_manana_vistas": round(sum(estados.get(r.rosa_id) == "lista_manana"
                                                    for r, v in pares if v.lista_manana) / len(vistas_manana), 3)
            if vistas_manana else None,
        }
    return {
        "rosas_reales": len(reales),
        "rosas_encontradas": len(rosas),
        "cobertura": round(len(usadas) / len(reales), 3) if reales else None,
        "duplicados": round(duplicadas / len(rosas), 3) if rosas else None,
        "falsas": falsas,
        "error_altura_cm": _media(err_altura),
        "error_metro_cm": _media(err_metro),
        "precision_optimo": round(aciertos_optimo / len(dice_optimo), 3) if dice_optimo else None,
        "recall_optimo": round(aciertos_optimo / len(reales_optimo), 3) if reales_optimo else None,
        "clase_correcta": round(sum(r.clase == v.estado for r, v in pares) / len(pares), 3) if pares else None,
        **extra,
    }
