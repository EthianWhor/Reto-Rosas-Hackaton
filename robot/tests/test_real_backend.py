"""Robot real: lo que se puede probar sin el robot (funciones sueltas y que el esqueleto cumpla la interfaz)."""

import math
from types import SimpleNamespace

import numpy as np
import pytest

from cuerpo import real_backend as rb
from cuerpo.interfaz import Cuerpo


def test_obstaculos_en_nube():
    puntos = np.array([
        [0.10, 0.0, 0.50],    # demasiado cerca: es el propio robot
        [1.20, 0.0, 0.30],    # caja en el camino: alto
        [0.80, 0.10, 0.02],   # manguera: bajo
        [0.60, 0.60, 0.80],   # rosal al costado, fuera del pasillo
        [0.70, 0.0, 1.50],    # alambre por encima
        [0.50, 0.0, 0.003],   # piso
    ])
    assert rb.obstaculos_en_nube(puntos, 1.5, 0.05) == (1.2, 0.8)
    assert rb.obstaculos_en_nube(puntos, 1.0, 0.05) == (None, 0.8)     # la caja está más lejos de lo que mira
    assert rb.obstaculos_en_nube(np.zeros((0, 3)), 1.5, 0.05) == (None, None)


def test_profundidad_y_camara():
    prof = rb.profundidad_a_metros(np.array([[0, 1500]], dtype=np.uint16))
    assert prof.tolist() == [[0.0, 1.5]]                                   # 0 sigue siendo "sin dato"
    # cámara de ROS mirando hacia +x del mundo (z óptico = +x, x óptico = −y, y óptico = −z)
    optica = np.array([[0, 0, 1], [-1, 0, 0], [0, -1, 0]], dtype=float)
    m = rb.optica_a_percepcion(optica)
    assert np.allclose(-m[:, 2], [1, 0, 0]) and np.allclose(m[:, 1], [0, 0, 1])   # mira hacia −z, arriba +y
    assert rb.fovy_desde_info(720, 720 / 2 / math.tan(math.radians(21.5))) == pytest.approx(43.0)


def test_velocidad_hacia():
    assert rb.velocidad_hacia((0, 0, 0), (2, 0), 0.3) == (0.3, 0.0)                 # derecho
    adelante, giro = rb.velocidad_hacia((0, 0, 0), (0, 2), 0.3)
    assert adelante == 0.0 and giro == rb.GIRO_MAX                                  # gira en el lugar a la izquierda
    assert rb.velocidad_hacia((0, 0, 0), (0.05, 0), 0.3)[0] == rb.VELOCIDAD_MIN_ARRANQUE   # cerca: no menos que el arranque
    assert rb.velocidad_hacia((1, 1, 0), (1.01, 1), 0.3) == (0.0, 0.0)              # llegó


def test_bateria():
    pmu = SimpleNamespace(battery_remaining_capacity_percentage=37, bms_status_bits=0b101)
    assert rb.bateria_pct(pmu) == 37.0 and rb.cargando(pmu)


def test_el_esqueleto_cumple_la_interfaz():
    abstractos = {n for n in dir(Cuerpo) if getattr(getattr(Cuerpo, n), "__isabstractmethod__", False)}
    assert not abstractos - set(vars(rb.CuerpoReal))       # implementa todo lo que pide la ronda
    with pytest.raises(RuntimeError, match="ROS 2"):       # aquí no hay ROS 2: avisa claro
        rb.CuerpoReal({})
    assert {que for que, _ in rb.pendientes()} >= {"pararse", "ir_a / orientar", "foto", "posar"}
