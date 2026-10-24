"""Invernadero a escala completa: física liviana, fotos con lo cercano y checkpoint con el tamaño."""

import numpy as np
import pytest

import configuracion
import ronda

mujoco = pytest.importorskip("mujoco")

from cuerpo.posturas import posturas                # noqa: E402
from cuerpo.sim_backend import CuerpoSim            # noqa: E402
from sim.escena_invernadero import armar_escena     # noqa: E402


@pytest.fixture(scope="module")
def cuerpo():
    cfg = configuracion.cargar(cambios={"sim.largo_cama_m": 20})
    c = CuerpoSim(armar_escena(cfg, 1), cfg)
    c.pararse()
    yield c
    c.cerrar()


def test_la_fisica_no_carga_las_plantas(cuerpo):
    assert cuerpo.mf.ngeom < cuerpo.m.ngeom / 5                      # solo robot, piso y camas
    assert (cuerpo.mf.nq, cuerpo.mf.nmocap) == (cuerpo.m.nq, cuerpo.m.nmocap)   # mismo robot


def test_la_foto_sale_de_donde_esta_el_robot(cuerpo):
    cuerpo.ir_a(6.0, cuerpo.posicion()[1])
    cuerpo.posar(list(posturas(cuerpo.cfg).values())[1])
    cap = cuerpo.foto()
    assert np.allclose(cap.cam_pos, cuerpo.df.cam_xpos[cuerpo.cam], atol=1e-3)   # el completo siguió al robot
    assert np.allclose(cap.cam_mat.ravel(), cuerpo.df.cam_xmat[cuerpo.cam], atol=1e-3)


def test_las_piezas_lejanas_no_cambian_lo_que_se_analiza(cuerpo):
    cuerpo.ir_a(10.0, cuerpo.posicion()[1])
    cuerpo.posar(list(posturas(cuerpo.cfg).values())[0])
    normal = cuerpo.foto()
    radio, cuerpo.radio_foto = cuerpo.radio_foto, 1e9                # dibujando todo
    try:
        todo = cuerpo.foto()
    finally:
        cuerpo.radio_foto = radio
    cerca = todo.profundidad < cuerpo.cfg["camara"]["distancia_max_m"]
    assert cerca.any() and np.allclose(normal.profundidad[cerca], todo.profundidad[cerca], atol=1e-3)
    assert (cuerpo.m.geom_group[cuerpo.piezas_fijas] == 1).all()     # después de la foto vuelven a verse


def test_el_checkpoint_guarda_el_tamano(tmp_path):
    cfg = configuracion.cargar()
    cfg["sim"]["camas"] = cfg["sim"]["largo_cama_m"] = None          # --completo
    datos = ronda.Avance.nuevo(tmp_path, cfg, [0]).datos
    assert datos["camas"] is None and datos["largo_cama_m"] is None
