"""Estado final de cada rosa: óptimo, lista mañana, inmaduro, pasado o dudosa (sección 2 del plan).

"Lista mañana" no la da el modelo: es una predicción sobre las inmaduras.

1. Candidata: clase inmaduro y p(óptimo) ≥ `p3_min_candidata`.
2. Tamaño: tamaño_rel = diámetro / diámetro típico de un punto 3.
3. Con historia (la misma rosa medida ayer):
       velocidad   = (hoy − ayer) / días
       días_faltan = (diámetro_punto3 − hoy) / velocidad   →  lista si ≤ `dias_max_lista_manana`
4. Sin historia (primera noche):
       puntaje = 0,6 · p(óptimo) + 0,4 · min(tamaño_rel, 1)   →  lista si ≥ `puntaje_lista_manana`
   El tamaño solo suma si tamaño_rel ≥ `tamano_rel_min` (si no, la cabeza todavía es pequeña).

Dudosa: si el modelo no está seguro (`seguro = false`), salvo cuando la duda es
solo entre inmaduro y óptimo (p(inmaduro) + p(óptimo) ≥ `duda_entre_vecinas_min`).
Esa duda es justo la de una rosa a punto de abrir, y se decide con las reglas
de "lista mañana" en vez de mandarla a revisión.
"""

from dataclasses import dataclass

ESTADOS = ["optimo", "lista_manana", "inmaduro", "pasado", "dudosa"]


@dataclass
class Madurez:
    estado: str
    tamano_rel: float | None = None
    puntaje: float | None = None
    dias_faltan: float | None = None
    motivo: str = ""


def tamano_relativo(diametro_cm: float, cfg: dict) -> float:
    return diametro_cm / cfg["rosas"]["diametro_punto3_cm"]


def dias_faltan(diametro_hoy: float, diametro_ayer: float, diametro_p3: float, dias: float = 1.0) -> float | None:
    """Días para llegar al tamaño de punto 3 al ritmo actual. None si no está creciendo."""
    velocidad = (diametro_hoy - diametro_ayer) / dias
    if velocidad <= 0:
        return None
    return max(0.0, (diametro_p3 - diametro_hoy) / velocidad)


def decidir(clase: str, seguro: bool, probs: dict, diametro_cm: float, cfg: dict,
            diametro_ayer_cm: float | None = None) -> Madurez:
    m = cfg["madurez"]
    p_inm, p_opt = probs.get("inmaduro", 0.0), probs.get("optimo", 0.0)
    duda_vecinas = clase == "inmaduro" and p_inm + p_opt >= m["duda_entre_vecinas_min"]

    if not seguro and not duda_vecinas:
        return Madurez("dudosa", motivo="el modelo no está seguro")
    if clase != "inmaduro":
        return Madurez(clase)

    rel = round(tamano_relativo(diametro_cm, cfg), 3)
    if p_opt < m["p3_min_candidata"]:
        return Madurez("inmaduro" if seguro else "dudosa", rel,
                       motivo="" if seguro else "el modelo no está seguro")

    if diametro_ayer_cm is not None:
        dias = dias_faltan(diametro_cm, diametro_ayer_cm, cfg["rosas"]["diametro_punto3_cm"])
        if dias is not None:
            lista = dias <= m["dias_max_lista_manana"]
            return Madurez("lista_manana" if lista else "inmaduro", rel, dias_faltan=round(dias, 2),
                           motivo=f"con historia: faltan {dias:.1f} días")

    suma_tamano = min(rel, 1.0) if rel >= m["tamano_rel_min"] else 0.0
    puntaje = round(0.6 * p_opt + 0.4 * suma_tamano, 3)
    lista = puntaje >= m["puntaje_lista_manana"]
    return Madurez("lista_manana" if lista else "inmaduro", rel, puntaje,
                   motivo=f"sin historia: puntaje {puntaje:.2f}")
