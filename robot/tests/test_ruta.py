"""Ruta en serpiente, giros del robot, lado según el rumbo y checkpoint para continuar la ronda."""

import json
import math

import pytest

import configuracion
import ronda
from navegacion.plano import armar_plano
from navegacion.ruta import SALIDA_M, camino_a_la_base, numero_parada, paradas, serpiente
from percepcion import geometria


@pytest.fixture(scope="module")
def cfg():
    return configuracion.cargar()


@pytest.fixture(scope="module")
def plano(cfg):
    return armar_plano(cfg)


def test_serpiente_alterna_el_sentido(cfg, plano):
    tramos = serpiente(plano, cfg, [0, 1, 2])
    assert [t.sentido for t in tramos] == [1, -1, 1]
    ida, vuelta = tramos[0], tramos[1]
    assert ida.xs[0] == 0 and ida.xs[-1] == plano.largo_m
    assert vuelta.xs == tuple(reversed(ida.xs))
    assert (ida.entrada_x, ida.salida_x) == (-SALIDA_M, plano.largo_m + SALIDA_M)
    assert vuelta.entrada_x == ida.salida_x        # entra por donde salió el anterior: no cruza camas
    assert vuelta.rumbo == pytest.approx(math.pi) and ida.rumbo == 0
    assert [t.y for t in tramos] == [plano.camino(k).y for k in (0, 1, 2)]


def test_numero_de_parada_igual_en_los_dos_sentidos(cfg, plano):
    xs = paradas(plano, cfg)
    assert [numero_parada(plano, cfg, x) for x in xs] == list(range(len(xs)))
    assert [numero_parada(plano, cfg, x) for x in reversed(xs)] == list(reversed(range(len(xs))))


def test_volver_a_la_base_sin_cruzar_camas(plano):
    base = (-1.2, 0.4)
    assert camino_a_la_base(plano, (-SALIDA_M, 3.9), base) == [base]
    # desde el pasillo del fondo vuelve por el mismo camino hasta la cabecera
    assert camino_a_la_base(plano, (plano.largo_m + SALIDA_M, 3.9), base) == [(-SALIDA_M, 3.9), base]


def test_lado_segun_el_rumbo(plano):
    y2 = plano.cama(2).y_centro
    assert geometria.asignar_cama(4.0, y2, plano, 1, rumbo=0.0)[1] == "izq"        # yendo al fondo
    assert geometria.asignar_cama(4.0, y2, plano, 1, rumbo=math.pi)[1] == "der"    # volviendo
    assert geometria.asignar_cama(4.0, y2, plano, 0, rumbo=0.0)[1] == "otra"       # desde un camino que no la toca


def test_checkpoint(tmp_path, cfg):
    carpeta = tmp_path / "rondas" / "INV1_2026-10-24_220000"
    carpeta.mkdir(parents=True)
    a = ronda.Avance.nuevo(carpeta, cfg, [0, 1, 2])
    a.marcar(1, 3.75)
    b = ronda.Avance.leer(carpeta)
    assert b.hecha(1, 3.75) and not b.hecha(1, 5.0) and b.caminos == [0, 1, 2]
    assert ronda.ultima_sin_terminar(tmp_path) == carpeta
    b.terminar()
    assert ronda.ultima_sin_terminar(tmp_path) is None


def test_robot_gira_y_camina_hacia_atras_por_el_camino(cfg):
    pytest.importorskip("mujoco")
    from cuerpo.sim_backend import CuerpoSim
    from sim.escena_invernadero import armar_escena
    escena = armar_escena(cfg, en_base=True)
    cuerpo = CuerpoSim(escena, cfg)
    try:
        cuerpo.pararse()
        assert cuerpo.posicion() == pytest.approx(tuple(cfg["sim"]["base_xy"]))
        y = escena.plano.camino(1).y
        cuerpo.ir_a(-SALIDA_M, y)                 # de la base a la entrada del camino 1
        cuerpo.ir_a(1.0, y)
        cuerpo.ir_a(0.2, y)                       # vuelve: gira 180° y camina hacia −x
        assert cuerpo.posicion() == pytest.approx((0.2, y), abs=1e-6)
        assert abs(cuerpo.rumbo()) == pytest.approx(math.pi, abs=1e-3)
        cap = cuerpo.foto()
        assert cap.rumbo == pytest.approx(cuerpo.rumbo())
        assert cap.cam_mat[:, 2][0] > 0.9         # la cámara (que mira hacia −z) apunta hacia −x
    finally:
        cuerpo.cerrar()


def test_ronda_interrumpida_y_continuada(tmp_path):
    """Batería baja después de 2 paradas, y luego sigue donde iba sin repetir fotos."""
    pytest.importorskip("mujoco")
    from cuerpo.sim_backend import CuerpoSim
    from percepcion import modelo_equipo
    from percepcion.analisis import crear_analizador
    from sim.escena_invernadero import armar_escena

    cfg = configuracion.cargar(cambios={"sim.largo_cama_m": 2.5, "sim.semilla": 3})
    plano = armar_plano(cfg)
    carpeta = tmp_path / "rondas" / "INV1_prueba"
    carpeta.mkdir(parents=True)
    avance = ronda.Avance.nuevo(carpeta, cfg, [0, 1])

    def correr(parar):
        escena = armar_escena(cfg, en_base=True)
        analizador = crear_analizador(cfg, modelo_equipo.elegir(cfg), plano, escena.verdad)
        cuerpo = CuerpoSim(escena, cfg)
        try:
            cuerpo.pararse()
            completa = ronda.recorrer(cuerpo, cfg, plano, ronda.GuardarCapturas(carpeta), avance, analizador,
                                      parar_despues=parar, avisar=lambda s: None)
            return completa, cuerpo.posicion()
        finally:
            cuerpo.cerrar()

    completa, donde = correr(2)
    assert not completa and len(avance.datos["hechas"]) == 2
    assert donde == pytest.approx(tuple(cfg["sim"]["base_xy"]))     # volvió a la base
    completa, donde = correr(None)
    n_paradas = len(paradas(plano, cfg)) * 2
    assert completa and len(avance.datos["hechas"]) == n_paradas
    assert json.loads((carpeta / "checkpoint.json").read_text(encoding="utf-8"))["terminada"]
    fotos = (carpeta / "capturas.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(fotos) == n_paradas * 4 and len({json.loads(f)["foto"] for f in fotos}) == len(fotos)
