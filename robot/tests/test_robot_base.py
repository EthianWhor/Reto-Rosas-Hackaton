"""Pruebas del paso 1 del robot: configuración, elección del modelo del equipo y escena."""

import math
import sys

import pytest

import configuracion
from percepcion import modelo_equipo

LISTO = {"listo": True, "motivo": "ok"}
NO_LISTO = {"listo": False, "motivo": "no existe"}


def cfg_con(**cambios):
    return configuracion.cargar(cambios={k.replace("__", "."): v for k, v in cambios.items()})


def test_config_por_defecto():
    cfg = configuracion.cargar()
    assert cfg["modo"] == "sim"
    assert cfg["percepcion"]["margen_recorte"] == 0.10
    assert cfg["percepcion"]["tamano_min_px"] == 32


def test_config_cambios_y_errores():
    assert cfg_con(percepcion__candidatas="color")["percepcion"]["candidatas"] == "color"
    with pytest.raises(ValueError):
        cfg_con(modo="volando")


def test_sim_con_figuras_usa_oraculo_aunque_haya_modelo():
    cfg = cfg_con()
    e = modelo_equipo.elegir(cfg, {"clasificador": LISTO, "detector": LISTO})
    assert (e["candidatas"], e["clasificador"]) == ("oraculo", "oraculo")


def test_hoy_sin_detector_usa_mascara_roja_y_rosanet():
    cfg = cfg_con(sim__rosas="cartel")
    e = modelo_equipo.elegir(cfg, {"clasificador": LISTO, "detector": NO_LISTO})
    assert (e["candidatas"], e["clasificador"]) == ("color", "rosanet")


def test_sin_pesos_en_sim_cae_al_oraculo_y_en_real_falla():
    estado = {"clasificador": NO_LISTO, "detector": NO_LISTO}
    assert modelo_equipo.elegir(cfg_con(sim__rosas="cartel"), estado)["clasificador"] == "oraculo"
    with pytest.raises(RuntimeError):
        modelo_equipo.elegir(cfg_con(modo="real"), estado)


def test_oraculo_no_existe_en_real():
    with pytest.raises(ValueError):
        modelo_equipo.elegir(cfg_con(modo="real", percepcion__candidatas="oraculo"),
                             {"clasificador": LISTO, "detector": NO_LISTO})


def test_detector_pedido_a_mano_sin_estar_listo_falla():
    with pytest.raises(RuntimeError):
        modelo_equipo.elegir(cfg_con(sim__rosas="cartel", percepcion__candidatas="detector_equipo"),
                             {"clasificador": LISTO, "detector": NO_LISTO})


def test_despues_del_pull_usa_el_detector_solo(tmp_path, monkeypatch):
    """Simula el git pull: aparece un módulo detector con sus pesos y `auto` lo toma sin tocar código."""
    paquete = tmp_path / "ml_nuevo"
    paquete.mkdir()
    (paquete / "__init__.py").write_text("")
    (paquete / "detect.py").write_text(
        "class RoseDetector:\n"
        "    def __init__(self, pesos):\n"
        "        self.pesos = pesos\n"
    )
    pesos = tmp_path / "detector.pt"
    pesos.write_bytes(b"")
    monkeypatch.syspath_prepend(str(tmp_path))

    cfg = cfg_con(modo="real", sim__rosas="cartel")
    cfg["modelo_equipo"]["detector"].update(modulo="ml_nuevo.detect", pesos=str(pesos))
    estado = modelo_equipo.revisar(cfg)
    assert estado["detector"]["listo"], estado["detector"]["motivo"]

    estado["clasificador"] = LISTO
    e = modelo_equipo.elegir(cfg, estado)
    assert (e["candidatas"], e["clasificador"]) == ("detector_equipo", "rosanet")

    cfg["modelo_equipo"]["detector"]["clasifica"] = True
    assert modelo_equipo.elegir(cfg, estado)["clasificador"] == "detector_equipo"
    assert modelo_equipo.cargar(cfg, "detector").pesos == pesos
    sys.modules.pop("ml_nuevo.detect", None)
    sys.modules.pop("ml_nuevo", None)


def test_revisar_dice_por_que_falta_algo():
    cfg = configuracion.cargar()
    cfg["modelo_equipo"]["detector"]["modulo"] = "ml.no_existe"
    cfg["modelo_equipo"]["clasificador"]["pesos"] = "runs/no_existe.pt"
    estado = modelo_equipo.revisar(cfg)
    assert "no existe el módulo" in estado["detector"]["motivo"]
    assert "faltan los pesos" in estado["clasificador"]["motivo"]


def test_fovy_desde_fov_horizontal():
    from sim.escena_invernadero import fovy_grados
    assert math.isclose(fovy_grados(70, 1920, 1080), 43.0, abs_tol=0.2)
    assert math.isclose(fovy_grados(70, 1280, 720), fovy_grados(70, 1920, 1080))


def test_escena_carga_robot_con_camara_a_la_altura_esperada():
    mujoco = pytest.importorskip("mujoco")
    from sim.escena_invernadero import CAMARA, armar_escena
    escena = armar_escena(configuracion.cargar())
    m, d = escena.m, escena.d
    assert m.nu > 0
    assert m.body("guia").mocapid[0] >= 0
    assert 1.1 < d.cam_xpos[m.camera(CAMARA).id][2] < 1.3  # ~1,19 m en el modelo de MuJoCo
    assert mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_LIGHT, "linterna") >= 0
