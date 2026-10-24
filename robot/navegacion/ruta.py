"""Dónde para el robot dentro de un camino (sección 4.4 del plan).

Por ahora el robot recorre los caminos que se le pidan, siempre hacia +x.
La ruta en serpiente por todo el invernadero (ida por un camino, vuelta por
el siguiente) llega cuando la escena tenga varios caminos.
"""

from navegacion.plano import Plano

SALIDA_M = 0.6   # cuánto camina después del fondo de la cama para salir del camino


def paradas(plano: Plano, cfg: dict) -> list[float]:
    """x de cada parada: 0, paso, 2·paso, … y siempre una al final de la cama."""
    paso = cfg["recorrido"]["paso_entre_paradas_m"]
    xs, x = [], 0.0
    while x < plano.largo_m - 1e-6:
        xs.append(round(x, 3))
        x += paso
    xs.append(plano.largo_m)
    return xs
