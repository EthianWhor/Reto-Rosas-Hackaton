"""Acción física: el robot apunta la cabeza a cada rosa óptima y la ilumina con el puntero."""

import pytest

import configuracion
import ronda
from percepcion.analisis import Deteccion
from percepcion.geometria import proyectar

mujoco = pytest.importorskip("mujoco")

from cuerpo.sim_backend import CuerpoSim          # noqa: E402
from sim.escena_invernadero import armar_escena   # noqa: E402


def test_apunta_a_la_rosa_y_apaga_el_puntero():
    cfg = configuracion.cargar()
    escena = armar_escena(cfg, 1)
    cuerpo = CuerpoSim(escena, cfg)
    try:
        cuerpo.pararse()
        y = escena.plano.camino(1).y
        cuerpo.ir_a(3.0, y)
        cerca = [r for r in escena.verdad if 2.5 < r.x < 4.0 and abs(r.y - y) < 0.8]
        a_mano = [r for r in cerca if r.z < 1.95]                  # más altas y encima del robot no alcanza
        for rosa in (min(a_mano, key=lambda r: r.z), max(a_mano, key=lambda r: r.z)):   # baja y alta
            assert cuerpo.senalar((rosa.x, rosa.y, rosa.z), 0.2)
            u, v, _ = proyectar((rosa.x, rosa.y, rosa.z), cuerpo.foto())
            assert abs(u - 960) < 60 and abs(v - 540) < 60          # la rosa queda en el centro de la foto
        assert not cuerpo.m.light_active[cuerpo.puntero]            # el puntero se apaga al terminar
        muy_alta = max(cerca, key=lambda r: r.z)
        assert not cuerpo.senalar((muy_alta.x, muy_alta.y, muy_alta.z), 0.2)   # avisa que no la centró
    finally:
        cuerpo.cerrar()


class CuerpoFalso:
    def __init__(self):
        self.senaladas = []

    def senalar(self, punto, segundos):
        self.senaladas.append(punto)
        return True


def det(clase, x, seguro=True):
    probs = {"inmaduro": 0.05, "optimo": 0.05, "pasado": 0.05, clase: 0.9}
    return Deteccion(foto="f.png", bbox=[0, 0, 50, 50], clase=clase, confianza=0.9 if seguro else 0.5,
                     seguro=seguro, probs=probs, x=x, y=0.0, altura_m=1.5, distancia_m=0.6,
                     metodo="profundidad", diametro_cm=5.0, cama=1, lado="izq", metro=x, tramo=1)


def test_senala_solo_optimas_seguras_y_una_vez(tmp_path):
    cfg = configuracion.cargar()
    avance = ronda.Avance.nuevo(tmp_path, cfg, [0])
    cuerpo = CuerpoFalso()
    dets = [det("optimo", 1.0), det("optimo", 1.03),            # la misma rosa vista en dos fotos
            det("optimo", 2.0, seguro=False), det("inmaduro", 3.0), det("pasado", 4.0)]
    assert ronda._senalar_optimas(cuerpo, cfg, dets, avance) == 1
    assert ronda._senalar_optimas(cuerpo, cfg, [det("optimo", 1.02)], avance) == 0   # ya señalada antes
    assert ronda.Avance.leer(tmp_path).senaladas == [[1.0, 0.0, 1.5]]                # queda en el checkpoint
    cfg["accion"]["tipo"] = "ninguna"
    assert ronda._senalar_optimas(cuerpo, cfg, [det("optimo", 5.0)], avance) == 0
