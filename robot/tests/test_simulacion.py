"""Pruebas del paso 2: plano, rosales, posturas, caminar y fotos en MuJoCo."""

import json
import math

import numpy as np
import pytest

import configuracion
from cuerpo import posturas as pos
from cuerpo.interfaz import Captura
from navegacion.plano import armar_plano, tramo
from navegacion.ruta import paradas

mujoco = pytest.importorskip("mujoco")


@pytest.fixture(scope="module")
def cfg():
    return configuracion.cargar()


@pytest.fixture(scope="module")
def escena(cfg):
    from sim.escena_invernadero import armar_escena
    return armar_escena(cfg)


@pytest.fixture(scope="module")
def cuerpo(escena, cfg):
    from cuerpo.sim_backend import CuerpoSim
    c = CuerpoSim(escena, cfg)
    c.pararse()
    yield c
    c.cerrar()


def test_plano_de_prueba(cfg):
    plano = armar_plano(cfg)
    assert len(plano.camas) == 2 and len(plano.caminos) == 3 and plano.largo_m == 10
    c1, c2, camino = plano.cama(1), plano.cama(2), plano.camino(1)
    assert (c1.y_min, c1.y_max) == pytest.approx((0.8, 1.8))
    assert c1.y_max < camino.y < c2.y_min
    assert camino.y - c1.y_max == pytest.approx(0.4)          # camino de 80 cm, robot al centro
    assert (camino.cama_der, camino.cama_izq) == (1, 2)
    assert plano.camino(0).cama_der is None and plano.camino(2).cama_izq is None


def test_plano_completo_en_modo_real():
    plano = armar_plano(configuracion.cargar(cambios={"modo": "real"}))
    assert len(plano.camas) == 20 and len(plano.caminos) == 21 and plano.largo_m == 30


def test_tramos():
    assert [tramo(m, 5) for m in (0, 4.99, 5, 12.35, 29.9)] == [1, 1, 2, 3, 6]


def test_paradas(cfg):
    xs = paradas(armar_plano(cfg), cfg)
    assert xs[0] == 0 and xs[-1] == 10 and len(xs) == 9
    assert all(b - a == pytest.approx(cfg["recorrido"]["paso_entre_paradas_m"]) for a, b in zip(xs, xs[1:]))


def test_posturas(cfg):
    p = pos.posturas(cfg)
    assert list(p) == pos.ORDEN
    alta = p["izq_alta"]
    assert alta["head_pitch"] + alta["waist_pitch"] == pytest.approx(cfg["recorrido"]["inclinacion_alta_rad"])
    assert alta["head_pitch"] == pytest.approx(pos.CABEZA_PITCH[0])   # la cabeza llega a su límite primero
    assert pos.CINTURA_PITCH[0] <= alta["waist_pitch"] <= 0
    assert p["izq_media"]["waist_yaw"] > 0 > p["der_media"]["waist_yaw"]
    assert p["izq_media"]["head_pitch"] == p["izq_media"]["waist_pitch"] == 0


def test_rosales_dentro_de_las_camas_y_repetibles(cfg, escena):
    from sim.escena_invernadero import armar_escena
    assert 2 * 10 * 8 <= len(escena.verdad) <= 2 * 10 * 12
    for r in escena.verdad:
        cama = escena.plano.cama(r.cama)
        assert cama.y_min - 0.05 < r.y < cama.y_max + 0.05
        assert cfg["rosas"]["altura_min_m"] <= r.z <= cfg["rosas"]["altura_max_m"]
        assert r.estado in {"inmaduro", "optimo", "pasado"}
        assert not r.lista_manana or r.estado == "inmaduro"
    assert {r.estado for r in escena.verdad} == {"inmaduro", "optimo", "pasado"}
    otra = armar_escena(cfg)
    assert [r.a_dict() for r in otra.verdad] == [r.a_dict() for r in escena.verdad]


def adelante(cap: Captura) -> np.ndarray:
    return -cap.cam_mat[:, 2]   # la cámara de MuJoCo mira hacia −z


def test_caminar_avanza_por_el_centro_del_camino(cuerpo, escena):
    x0, y0 = cuerpo.posicion()
    cuerpo.caminar_hasta(x0 + 0.3)
    x, y = cuerpo.posicion()
    assert x == pytest.approx(x0 + 0.3) and y == pytest.approx(escena.plano.camino(1).y)
    assert cuerpo.foto().cam_pos[0] > x0 + 0.2   # el cuerpo siguió al punto guía


@pytest.mark.parametrize("nombre, signo_y, mira_arriba", [
    ("izq_media", 1, False), ("izq_alta", 1, True), ("der_alta", -1, True), ("der_media", -1, False)])
def test_posturas_apuntan_donde_deben(cuerpo, cfg, nombre, signo_y, mira_arriba):
    reales = cuerpo.posar(pos.posturas(cfg)[nombre])
    v = adelante(cuerpo.foto())
    giro = math.degrees(math.atan2(v[1], v[0]))
    elevacion = math.degrees(math.asin(v[2]))
    assert giro * signo_y == pytest.approx(math.degrees(cfg["recorrido"]["giro_diagonal_rad"]), abs=3)
    assert (elevacion > 25) if mira_arriba else (abs(elevacion) < 5)
    assert reales["waist_yaw"] * signo_y > 0.5


def test_foto_y_profundidad_coinciden_con_las_rosas(cuerpo, escena, cfg):
    """Proyecta las rosas de la verdad a la foto y revisa que la profundidad diga la misma distancia.
    Así se comprueba la convención de la cámara que va a usar la geometría (píxel → 3D)."""
    cuerpo.posar(pos.posturas(cfg)["izq_media"])
    cap = cuerpo.foto()
    alto, ancho = cfg["camara"]["sim_alto"], cfg["camara"]["sim_ancho"]
    assert cap.rgb.shape == (alto, ancho, 3) and cap.profundidad.shape == (alto, ancho)
    k = cap.intrinsecos()
    revisadas = aciertos = 0
    for r in escena.verdad:
        p = cap.cam_mat.T @ (np.array([r.x, r.y, r.z]) - cap.cam_pos)   # en ejes de la cámara
        z = -p[2]
        if z < 0.3:
            continue
        u = k["cx"] + k["f"] * p[0] / z
        v = k["cy"] - k["f"] * p[1] / z
        if not (5 <= u < cap.ancho - 5 and 5 <= v < cap.alto - 5):
            continue
        revisadas += 1
        medida = cap.profundidad[int(v), int(u)]
        assert medida <= z + 0.05          # nunca hay algo "detrás" de la rosa en su píxel
        aciertos += abs(medida - z) < 0.04  # si no está tapada, la profundidad es la de la rosa
    assert revisadas >= 5
    assert aciertos / revisadas > 0.5


def test_guardar_capturas(tmp_path):
    import ronda
    from PIL import Image
    prof = np.full((4, 6), 2.5, dtype=np.float32)
    prof[0, 0] = 1000.0   # cielo
    cap = Captura(np.zeros((4, 6, 3), np.uint8), prof, np.array([1.0, 2.0, 1.2]), np.eye(3), 43.0, (1.0, 2.0),
                  {"waist_yaw": 0.61})
    g = ronda.GuardarCapturas(tmp_path)
    fila = g.guardar(cap, camino=1, parada=2, postura="izq_alta")
    assert (tmp_path / "fotos" / "c01_p02_izq_alta.png").exists()
    mm = np.array(Image.open(tmp_path / fila["profundidad"]))
    assert mm[0, 0] == 0 and mm[1, 1] == 2500
    guardada = json.loads((tmp_path / "capturas.jsonl").read_text(encoding="utf-8"))
    assert guardada["postura"] == "izq_alta" and guardada["cam_pos"] == [1.0, 2.0, 1.2]
    assert guardada["f"] == pytest.approx(2 / math.tan(math.radians(43) / 2))
