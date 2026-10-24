"""Las 4 posturas de cada parada (sección 3.2 del plan).

El giro lo hace la cintura (que gira mucho más que la cabeza). La inclinación
hacia arriba la hace primero la cabeza, hasta su límite, y el resto la cintura
(solo con el robot quieto). En el X2, "mirar hacia arriba" es un ángulo
**negativo** en la cabeza y en la cintura (comprobado en la simulación).
"""

# Límites de X2-Ultra.xml (radianes)
CABEZA_PITCH = (-0.401425, 0.488692)
CINTURA_PITCH = (-0.314159, 0.314159)
CINTURA_YAW = (-3.429572, 2.120575)

# Orden en que se toman: así la cintura gira una sola vez de lado a lado.
ORDEN = ["izq_media", "izq_alta", "der_alta", "der_media"]
NEUTRA = {"waist_yaw": 0.0, "waist_pitch": 0.0, "head_yaw": 0.0, "head_pitch": 0.0}


def _limitar(valor: float, limites: tuple[float, float]) -> float:
    return min(max(valor, limites[0]), limites[1])


def repartir_inclinacion(inclinacion: float) -> tuple[float, float]:
    """(cabeza, cintura) que suman `inclinacion`, con la cabeza primero."""
    cabeza = _limitar(inclinacion, CABEZA_PITCH)
    cintura = _limitar(inclinacion - cabeza, CINTURA_PITCH)
    return cabeza, cintura


def limites_inclinacion() -> tuple[float, float]:
    """Cuánto puede inclinarse la cámara sumando cabeza y cintura."""
    return CABEZA_PITCH[0] + CINTURA_PITCH[0], CABEZA_PITCH[1] + CINTURA_PITCH[1]


def posturas(cfg: dict) -> dict[str, dict]:
    rec = cfg["recorrido"]
    giro = _limitar(rec["giro_diagonal_rad"], CINTURA_YAW)
    cabeza_alta, cintura_alta = repartir_inclinacion(rec["inclinacion_alta_rad"])
    resultado = {}
    for nombre in ORDEN:
        lado, altura = nombre.split("_")
        alta = altura == "alta"
        resultado[nombre] = {
            "waist_yaw": giro if lado == "izq" else -giro,
            "waist_pitch": cintura_alta if alta else 0.0,
            "head_yaw": 0.0,
            "head_pitch": cabeza_alta if alta else 0.0,
        }
    return resultado
