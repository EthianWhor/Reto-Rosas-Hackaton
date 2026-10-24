"""La tabla única de la ronda (sección 10 del plan).

El Excel y el JSON salen de aquí, así nunca dicen cosas distintas. Nombres de
columnas en minúscula, sin tildes y con guion bajo, para que el dashboard los
lea sin problemas. Los estados se llaman como en RosaNet y en el juego de la
tablet: inmaduro, optimo, pasado, más lista_manana y dudosa.
"""

import math
from dataclasses import dataclass, field

from navegacion.plano import Plano
from percepcion.dedup import Rosa, cuadrante_id
from percepcion.madurez import ESTADOS, decidir

COLUMNAS_CUADRANTES = ["cuadrante_id", "cama", "tramo", "desde_m", "hasta_m", "optimo", "lista_manana",
                       "inmaduro", "pasado", "dudosa", "total", "prioridad", "orden"]
COLUMNAS_LISTAS = ["rosa_id", "estado", "cuadrante_id", "cama", "lado", "metro_en_cama", "altura_m",
                   "diametro_cm", "confianza", "foto", "fecha_hora"]
COLUMNAS_TODAS = COLUMNAS_LISTAS[:-2] + ["p_inmaduro", "p_optimo", "p_pasado", "tamano_rel", "puntaje_manana",
                                         "vistas", "foto", "fecha_hora"]
COLUMNAS_DUDOSAS = ["rosa_id", "clase_modelo", "confianza", "cuadrante_id", "cama", "lado", "metro_en_cama",
                    "altura_m", "foto", "fecha_hora"]

DICCIONARIO = [
    ("cuadrante_id", "Invernadero-cama-tramo. INV1-C07-T3 = invernadero 1, cama 7, tramo 3 (de 10 a 15 m)"),
    ("tramo", "Pedazo de 5 m de cama. T1 = 0–5 m, T2 = 5–10 m, …"),
    ("optimo", "Punto 3, punto de corte: cortar hoy"),
    ("lista_manana", "Inmadura a punto de abrir: cortar mañana (predicción del robot, no del modelo)"),
    ("inmaduro", "Punto 1–2, cerrada: no cortar"),
    ("pasado", "Sobreabierta: se pasó el punto de corte (pérdida)"),
    ("dudosa", "El modelo no estaba seguro: una persona debe revisar la foto"),
    ("prioridad", "alta = hay varias rosas para cortar hoy; media = hay alguna para hoy o mañana; baja = nada"),
    ("orden", "Orden de visita sugerido para la pantalla de la entrada (1 = primero)"),
    ("lado", "De qué lado del robot estaba la cama cuando la vio (izq / der)"),
    ("metro_en_cama", "Metros desde la cabecera de la cama (pasillo principal)"),
    ("altura_m", "Altura de la cabeza de la rosa sobre el piso"),
    ("diametro_cm", "Diámetro estimado de la cabeza"),
    ("confianza", "Confianza del modelo en su clase (0 a 1)"),
    ("tamano_rel", "Diámetro / diámetro típico de un punto 3"),
    ("puntaje_manana", "Puntaje de 'lista mañana' (≥ 0,6 = lista mañana)"),
    ("vistas", "En cuántas fotos se vio la misma rosa"),
]


@dataclass
class Reporte:
    id_ronda: str
    invernadero: str
    fecha: str                       # YYYY-MM-DD de la ronda
    inicio: str
    fin: str
    cuadrantes: list[dict]
    rosas_listas: list[dict]
    todas: list[dict]
    dudosas: list[dict]
    ronda: list[tuple[str, object]]
    obstaculos: list[str] = field(default_factory=list)
    diccionario: list[tuple[str, str]] = field(default_factory=lambda: list(DICCIONARIO))


def prioridad(optimo: int, lista_manana: int, minimo_alta: int) -> str:
    if optimo >= minimo_alta:
        return "alta"
    if optimo or lista_manana:
        return "media"
    return "baja"


def armar_cuadrantes(estados: list[tuple[Rosa, str]], plano: Plano, camas: set[int], cfg: dict) -> list[dict]:
    inv = cfg["invernadero"]["id"]
    n_tramos = math.ceil(plano.largo_m / plano.tramo_m)
    filas = {}
    for cama in sorted(camas):
        for t in range(1, n_tramos + 1):
            cid = cuadrante_id(inv, cama, t)
            filas[cid] = {"cuadrante_id": cid, "cama": cama, "tramo": t,
                          "desde_m": round((t - 1) * plano.tramo_m, 2),
                          "hasta_m": round(min(t * plano.tramo_m, plano.largo_m), 2),
                          **{e: 0 for e in ESTADOS}, "total": 0}
    for rosa, estado in estados:
        fila = filas.get(rosa.cuadrante_id)
        if fila is not None:
            fila[estado] += 1
            fila["total"] += 1
    minimo_alta = cfg["reporte"]["optimo_prioridad_alta"]
    for fila in filas.values():
        fila["prioridad"] = prioridad(fila["optimo"], fila["lista_manana"], minimo_alta)
    # orden de visita: más rosas para hoy primero (las de mañana valen la mitad)
    puntaje = lambda f: f["optimo"] + 0.5 * f["lista_manana"]
    for k, fila in enumerate(sorted(filas.values(), key=lambda f: (-puntaje(f), f["cuadrante_id"])), start=1):
        fila["orden"] = k
    return [{c: f[c] for c in COLUMNAS_CUADRANTES} for f in filas.values()]


def armar_reporte(rosas: list[Rosa], plano: Plano, camas: set[int], cfg: dict, meta: dict) -> Reporte:
    """meta: id_ronda, inicio, fin, fechas_fotos (foto → fecha_hora), ronda (lista de (campo, valor)), obstaculos."""
    fechas = meta.get("fechas_fotos", {})
    estados, listas, todas, dudosas = [], [], [], []
    for r in rosas:
        m = decidir(r.clase, r.seguro, r.probs, r.diametro_cm, cfg)
        estados.append((r, m.estado))
        base = {"rosa_id": r.rosa_id, "estado": m.estado, "cuadrante_id": r.cuadrante_id, "cama": r.cama,
                "lado": r.lado, "metro_en_cama": round(r.metro, 2), "altura_m": round(r.altura_m, 2),
                "diametro_cm": round(r.diametro_cm, 1), "confianza": r.confianza, "foto": r.foto,
                "fecha_hora": fechas.get(r.foto, "")}
        todas.append({**base, "p_inmaduro": r.probs.get("inmaduro"), "p_optimo": r.probs.get("optimo"),
                      "p_pasado": r.probs.get("pasado"), "tamano_rel": m.tamano_rel,
                      "puntaje_manana": m.puntaje, "vistas": r.vistas})
        if m.estado in ("optimo", "lista_manana"):
            listas.append(base)
        if m.estado == "dudosa":
            dudosas.append({"rosa_id": r.rosa_id, "clase_modelo": r.clase, "confianza": r.confianza,
                            "cuadrante_id": r.cuadrante_id, "cama": r.cama, "lado": r.lado,
                            "metro_en_cama": round(r.metro, 2), "altura_m": round(r.altura_m, 2),
                            "foto": r.foto, "fecha_hora": base["fecha_hora"]})
    # las de hoy primero; dentro de cada estado, por cama y metro (el orden en que las encuentra un operario)
    listas.sort(key=lambda f: (f["estado"] != "optimo", f["cama"], f["metro_en_cama"]))
    return Reporte(
        id_ronda=meta["id_ronda"], invernadero=cfg["invernadero"]["id"], fecha=meta["inicio"][:10],
        inicio=meta["inicio"], fin=meta["fin"],
        cuadrantes=armar_cuadrantes(estados, plano, camas, cfg),
        rosas_listas=[{c: f[c] for c in COLUMNAS_LISTAS} for f in listas],
        todas=[{c: f[c] for c in COLUMNAS_TODAS} for f in todas],
        dudosas=dudosas, ronda=meta.get("ronda", []), obstaculos=meta.get("obstaculos", []))
