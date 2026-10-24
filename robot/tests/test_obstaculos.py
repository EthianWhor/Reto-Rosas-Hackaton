"""Escena realista (postes, mangueras, desniveles) y obstáculos en el camino."""

import pytest

import configuracion
import ronda
from navegacion.plano import armar_plano
from navegacion.ruta import paradas, serpiente

mujoco = pytest.importorskip("mujoco")

from cuerpo.sim_backend import CuerpoSim          # noqa: E402
from sim.escena_invernadero import armar_escena   # noqa: E402


def cfg_con(**cambios):
    return configuracion.cargar(cambios={k.replace("__", "."): v for k, v in cambios.items()})


def test_estructura_en_la_escena_sin_cambiar_las_rosas():
    con = armar_escena(cfg_con())
    sin = armar_escena(cfg_con(sim__estructura={"postes": False, "mangueras_por_camino": [0, 0],
                                                "desniveles_por_camino": [0, 0]}, sim__obstaculos=[]))
    nombres = [con.m.geom(g).name for g in range(con.m.ngeom)]
    assert any(n.startswith("poste_") for n in nombres) and any(n.startswith("alambre_") for n in nombres)
    assert any(n.startswith("manguera_") for n in nombres)
    assert [o.nombre for o in con.obstaculos] == ["obstaculo0", "obstaculo1"] and not sin.obstaculos
    assert [r.a_dict() for r in con.verdad] == [r.a_dict() for r in sin.verdad]   # mismas rosas


def test_sensor_ve_el_obstaculo_y_las_mangueras():
    cfg = cfg_con()
    escena = armar_escena(cfg, 2)
    cuerpo = CuerpoSim(escena, cfg)
    try:
        cuerpo.pararse()
        y = escena.plano.camino(2).y
        cuerpo.ir_a(2.5, y)
        alto, _ = cuerpo.obstaculos_adelante(3.0)
        assert alto == pytest.approx(4.4 - 0.2 - 2.5, abs=0.02)      # cara de la caja (40 cm de lado)
        assert cuerpo.obstaculos_adelante(1.0)[0] is None              # más lejos de lo que mira
        cuerpo.orientar(3.14159)
        assert cuerpo.obstaculos_adelante(3.0)[0] is None               # hacia atrás no hay nada alto
    finally:
        cuerpo.cerrar()


def test_serpiente_desde_el_fondo():
    cfg = cfg_con()
    tramos = serpiente(armar_plano(cfg), cfg, [1, 2], desde_cabecera=False)
    assert [t.sentido for t in tramos] == [-1, 1]


def correr(cfg, carpeta, caminos):
    escena = armar_escena(cfg, en_base=True)
    avance = ronda.Avance.nuevo(carpeta, cfg, caminos)
    cuerpo = CuerpoSim(escena, cfg)
    try:
        cuerpo.pararse()
        completa = ronda.recorrer(cuerpo, cfg, escena.plano, ronda.GuardarCapturas(carpeta), avance,
                                  avisar=lambda s: None)
        return completa, avance, cuerpo.posicion()
    finally:
        cuerpo.cerrar()


def test_obstaculo_que_quitan_y_obstaculo_que_bloquea(tmp_path):
    import main
    cfg = cfg_con(sim__largo_cama_m=5, recorrido__espera_obstaculo_s=10, sim__obstaculos=[
        {"camino": 0, "x": 3.0, "alto_m": 0.4},                    # se queda: bloquea el camino 0
        {"camino": 1, "x": 1.9, "alto_m": 0.3, "se_quita_s": 5}])  # lo quitan mientras espera
    carpeta = tmp_path / "rondas" / "x"
    carpeta.mkdir(parents=True)
    completa, avance, donde = correr(cfg, carpeta, [0, 1])
    assert completa and donde == pytest.approx(tuple(cfg["sim"]["base_xy"]))
    assert [(o["camino"], o["resultado"]) for o in avance.obstaculos] == [(0, "bloqueado"), (1, "lo quitaron")]
    plano = armar_plano(cfg)
    hechas_0 = [x for c, x in avance.datos["hechas"] if c == 0]
    assert hechas_0 == [0.0, 1.25]                                  # no llegó a 2,5: frena a 50 cm de la caja
    assert len([1 for c, _ in avance.datos["hechas"] if c == 1]) == len(paradas(plano, cfg))   # camino 1 completo
    assert main.cuadrantes_bloqueados(avance.obstaculos, plano, cfg) == ["INV1-C01-T1"]


def test_dos_rondas_en_el_mismo_segundo_no_comparten_carpeta(tmp_path):
    cfg = cfg_con()
    a, b = ronda.nueva_carpeta(cfg, tmp_path), ronda.nueva_carpeta(cfg, tmp_path)
    assert a != b and a.is_dir() and b.is_dir()
