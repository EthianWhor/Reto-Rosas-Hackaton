"""Pruebas del paso 3: geometría píxel → 3D, oráculo, deduplicación y métricas."""

import random

import numpy as np
import pytest

import configuracion
import metricas
from cuerpo.interfaz import Captura
from navegacion.plano import armar_plano
from percepcion import geometria
from percepcion.analisis import Deteccion
from percepcion.candidatas import Candidata
from percepcion.clasificador import ClasificadorOraculo
from percepcion.dedup import juntar
from sim.rosas import RosaVerdad


@pytest.fixture(scope="module")
def cfg():
    return configuracion.cargar()


@pytest.fixture(scope="module")
def plano(cfg):
    return armar_plano(cfg)


def captura_mirando_izquierda(plano, prof=None) -> Captura:
    """Cámara a 1,2 m en el centro del camino 1, mirando hacia +y (la cama 2), sin inclinar."""
    y = plano.camino(1).y
    # ejes de la cámara en el mundo: x de la cámara = −x del mundo, y = arriba, mira hacia −z = +y del mundo
    mat = np.array([[-1, 0, 0], [0, 0, -1], [0, 1, 0]], dtype=float)
    return Captura(np.zeros((108, 192, 3), np.uint8), prof, np.array([3.0, y, 1.2]), mat, 43.0, (3.0, y))


def test_proyectar_y_volver_da_el_mismo_punto(plano):
    cap = captura_mirando_izquierda(plano)
    punto = np.array([3.2, plano.cama(2).y_centro, 1.6])
    u, v, z = geometria.proyectar(punto, cap)
    assert z == pytest.approx(punto[1] - cap.cam_pos[1])
    assert np.allclose(geometria.punto_desde_pixel(u, v, z, cap), punto)


def test_profundidad_caja_ignora_ceros():
    prof = np.zeros((20, 20), np.float32)
    prof[8:12, 8:12] = 1.5
    assert geometria.profundidad_caja(prof, (0, 0, 20, 20)) == pytest.approx(1.5)
    assert geometria.profundidad_caja(np.zeros((20, 20)), (0, 0, 20, 20)) is None


def test_profundidad_caja_ignora_una_hoja_delante():
    prof = np.full((20, 20), 1.50, np.float32)   # la rosa
    prof[6:14, 6:12] = 0.70                      # una hoja tapa el 75 % del centro
    assert geometria.profundidad_caja(prof, (0, 0, 20, 20)) == pytest.approx(1.50)


def test_ubicar_con_profundidad_y_sin_ella(plano):
    punto = np.array([3.2, plano.cama(2).y_centro, 1.6])
    sin_prof = captura_mirando_izquierda(plano)
    u, v, z = geometria.proyectar(punto, sin_prof)
    medio = 0.025 * sin_prof.intrinsecos()["f"] / z      # cabeza de 5 cm
    bbox = (u - medio, v - medio, u + medio, v + medio)

    prof = np.full((108, 192), z, np.float32)
    con_prof = captura_mirando_izquierda(plano, prof)
    ub = geometria.ubicar(bbox, con_prof, plano, camino=1)
    assert ub.metodo == "profundidad"
    assert (ub.x, ub.y, ub.z) == pytest.approx(tuple(punto), abs=1e-3)
    assert (ub.cama, ub.lado, ub.tramo) == (2, "izq", 1)
    assert ub.diametro_cm == pytest.approx(5.0, abs=0.05)

    # plan B: el rayo se corta con el centro de la cama, que es justo donde está el punto
    ub_b = geometria.ubicar(bbox, sin_prof, plano, camino=1)
    assert ub_b.metodo == "plano"
    assert (ub_b.x, ub_b.z) == pytest.approx((punto[0], punto[2]), abs=1e-3)


def test_asignar_cama(plano):
    y1, y2 = plano.cama(1).y_centro, plano.cama(2).y_centro
    assert geometria.asignar_cama(12.0, y2, plano, 1) == (2, "izq", 10.0, 2)   # metro se recorta al largo
    assert geometria.asignar_cama(4.0, y1, plano, 1)[:2] == (1, "der")
    assert geometria.asignar_cama(4.0, plano.camino(1).y, plano, 1) is None     # en medio del camino


def det(x, alt, conf, dist=1.5, clase="optimo", foto="f.png") -> Deteccion:
    return Deteccion(foto, [0, 0, 40, 40], clase, conf, conf >= 0.6, {}, x, 2.9, alt, dist, "profundidad",
                     5.0, 2, "izq", x, 1)


def test_dedup_junta_las_cercanas_y_se_queda_la_mejor():
    rosas = juntar([det(3.00, 1.50, 0.7, foto="a"), det(3.04, 1.52, 0.9, foto="b"), det(3.30, 1.50, 0.8)],
                   radio_m=0.08, invernadero="INV1")
    assert len(rosas) == 2
    junta = next(r for r in rosas if r.vistas == 2)
    assert junta.confianza == 0.9 and junta.foto == "b" and set(junta.fotos) == {"a", "b"}
    assert junta.rosa_id == "INV1-C02-T1-3.04-1.52" and junta.cuadrante_id == "INV1-C02-T1"


def test_clasificador_oraculo(cfg):
    verdad = [RosaVerdad(0, "optimo", False, 2, 0, 0, 1.5, 5.0), RosaVerdad(1, "inmaduro", True, 2, 0, 0, 1.5, 4.5)]
    c = dict(cfg, oraculo={**cfg["oraculo"], "errores_clase": 0.0})
    clf = ClasificadorOraculo(verdad, c, random.Random(1), umbral_seguro=0.6)
    res = clf.clasificar(None, [Candidata((0, 0, 40, 40), 0), Candidata((0, 0, 40, 40), 1)])
    assert [r["clase"] for r in res] == ["optimo", "inmaduro"]
    for r in res:
        assert sum(r["probs"].values()) == pytest.approx(1, abs=0.01)
        assert r["seguro"] == (r["confianza"] >= 0.6)
    lista = res[1]["probs"]
    assert lista["optimo"] > lista["pasado"]   # la "lista mañana" se parece más a óptimo


def test_metricas():
    from percepcion.dedup import Rosa
    verdad = [RosaVerdad(0, "optimo", False, 2, 3.0, 2.9, 1.5, 5.0), RosaVerdad(1, "inmaduro", False, 2, 5.0, 2.9, 1.2, 4.0)]
    def rosa(x, alt, clase, conf):
        return Rosa("id", "c", clase, conf, True, {}, 2, 1, "izq", x, alt, x, 2.9, 5.0, 1.5, "f")
    m = metricas.comparar([rosa(3.02, 1.51, "optimo", 0.9), rosa(3.0, 1.5, "optimo", 0.8), rosa(8.0, 1.0, "pasado", 0.7)],
                          verdad, {2})
    assert m["cobertura"] == 0.5 and m["falsas"] == 1 and m["duplicados"] == pytest.approx(1 / 3, abs=0.001)
    assert m["error_altura_cm"] == pytest.approx(1.0) and m["precision_optimo"] == 1.0 and m["recall_optimo"] == 1.0


def test_parada_real_en_mujoco_ubica_bien_las_rosas(cfg):
    pytest.importorskip("mujoco")
    from cuerpo.posturas import posturas
    from cuerpo.sim_backend import CuerpoSim
    from percepcion import modelo_equipo
    from percepcion.analisis import crear_analizador
    from sim.escena_invernadero import armar_escena

    escena = armar_escena(cfg)
    analizador = crear_analizador(cfg, modelo_equipo.elegir(cfg), escena.plano, escena.verdad)
    cuerpo = CuerpoSim(escena, cfg)
    try:
        cuerpo.pararse()
        cuerpo.caminar_hasta(2.5)
        for p in posturas(cfg).values():
            cuerpo.posar(p)
            analizador.analizar(cuerpo.foto(), "f.png", escena.camino)
    finally:
        cuerpo.cerrar()
    dets = analizador.detecciones
    assert len(dets) >= 10
    reales = {r.id: r for r in escena.verdad}
    for d in dets:
        r = reales[d.verdad_id]
        assert abs(d.altura_m - r.z) < 0.05 and abs(d.x - r.x) < 0.05
        assert d.cama == r.cama
