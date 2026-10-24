"""El robot usando el modelo del equipo (detector + RosaNet) y los carteles de la simulación."""

import glob

import numpy as np
import pytest
from PIL import Image

import configuracion
from cuerpo.interfaz import Captura
from percepcion import modelo_equipo
from percepcion.candidatas import Candidata, CandidatasColor, CandidatasDetector
from percepcion.clasificador import ClasificadorRosaNet, clase_robot


def captura(rgb) -> Captura:
    return Captura(rgb, None, np.zeros(3), np.eye(3), 43.0, (0.0, 0.0))


def test_clase_robot():
    assert clase_robot("2_optimo") == "optimo"
    assert clase_robot("1_inmaduro") == "inmaduro" and clase_robot("3_pasado") == "pasado"


class PredictorFalso:
    def __init__(self):
        self.recortes = []

    def predict(self, recorte):
        self.recortes.append(recorte.size)
        return {"etapa": "2_optimo", "confianza": 0.8, "seguro": True,
                "probabilidades": {"1_inmaduro": 0.15, "2_optimo": 0.8, "3_pasado": 0.05}, "tips": {"mirar": []}}


def test_rosanet_recorta_con_15_por_ciento_y_traduce_las_clases():
    pytest.importorskip("torch")
    pred = PredictorFalso()
    clf = ClasificadorRosaNet(pred, margen=0.15)
    res = clf.clasificar(captura(np.zeros((200, 300, 3), np.uint8)), [Candidata((100, 50, 140, 90))])
    assert pred.recortes == [(52, 52)]                 # 40 px + 15 % a cada lado (pad_box del equipo)
    assert res[0]["clase"] == "optimo" and res[0]["probs"] == {"inmaduro": 0.15, "optimo": 0.8, "pasado": 0.05}


def test_aclarar_fondo_solo_pinta_lo_que_esta_detras_de_la_rosa():
    from percepcion.clasificador import aclarar_fondo
    rgb = np.full((100, 100, 3), 10, np.uint8)            # noche: todo oscuro
    prof = np.full((100, 100), 6.0, np.float32)           # fondo lejos
    prof[40:60, 40:60] = 1.5                               # la rosa
    prof[45:50, 30:40] = 1.2                               # una hoja delante, a la izquierda
    prof[0:5, :] = 0                                       # sin dato
    rec = aclarar_fondo(rgb, prof, (40, 40, 60, 60), (0, 0, 100, 100), (170, 175, 180), 0.25)
    assert tuple(rec[50, 50]) == (10, 10, 10)              # la rosa no se toca
    assert tuple(rec[47, 35]) == (10, 10, 10)              # la hoja delante tampoco
    assert tuple(rec[80, 80]) == (170, 175, 180)           # el fondo lejano sí
    assert tuple(rec[2, 50]) == (170, 175, 180)            # y lo que no tiene dato
    assert aclarar_fondo(rgb, None, (40, 40, 60, 60), (0, 0, 100, 100), (170, 175, 180), 0.25).max() == 10


def test_rosanet_recibe_el_fondo_aclarado_si_esta_activo():
    pytest.importorskip("torch")

    class Guarda(PredictorFalso):
        def predict(self, recorte):
            self.ultimo = np.asarray(recorte)
            return super().predict(recorte)

    rgb = np.full((200, 300, 3), 10, np.uint8)
    prof = np.full((200, 300), 6.0, np.float32)
    prof[50:90, 100:140] = 1.5
    cap = Captura(rgb, prof, np.zeros(3), np.eye(3), 43.0, (0.0, 0.0))
    pred = Guarda()
    fondo = {"activo": True, "color": [170, 175, 180], "mas_lejos_m": 0.25}
    ClasificadorRosaNet(pred, 0.15, fondo).clasificar(cap, [Candidata((100, 50, 140, 90))])
    assert tuple(pred.ultimo[0, 0]) == (170, 175, 180) and tuple(pred.ultimo[26, 26]) == (10, 10, 10)
    ClasificadorRosaNet(pred, 0.15, {**fondo, "activo": False}).clasificar(cap, [Candidata((100, 50, 140, 90))])
    assert tuple(pred.ultimo[0, 0]) == (10, 10, 10)


def test_detector_recibe_rgb_y_da_candidatas():
    class DetectorFalso:
        def detect(self, img):
            assert isinstance(img, np.ndarray) and img.shape[2] == 3
            return [{"bbox": [10.4, 20.6, 50.2, 61.0], "confianza": 0.43}]
    c = CandidatasDetector(DetectorFalso()).buscar(captura(np.zeros((100, 100, 3), np.uint8)))
    assert c[0].bbox == (10, 21, 50, 61) and c[0].confianza_deteccion == 0.43


def test_candidatas_por_color():
    rgb = np.zeros((120, 200, 3), np.uint8)
    rgb[20:50, 30:60] = (200, 20, 30)      # una mancha roja
    rgb[70:100, 120:150] = (30, 160, 40)   # una hoja verde
    cands = CandidatasColor().buscar(captura(rgb))
    assert len(cands) == 1 and cands[0].bbox == (30, 20, 60, 50)


def test_modelo_del_equipo_listo_con_los_pesos_de_git():
    estado = modelo_equipo.revisar(configuracion.cargar())
    if not all(e["listo"] for e in estado.values()):
        pytest.skip(f"falta instalar algo: {estado}")
    e = modelo_equipo.elegir(configuracion.cargar(cambios={"sim.rosas": "cartel"}), estado)
    assert (e["candidatas"], e["clasificador"]) == ("detector_equipo", "rosanet")


def test_rosanet_de_verdad_con_una_foto_de_la_finca():
    """Contrato desde el lado del robot, con los pesos reales de modelos/."""
    pytest.importorskip("torch")
    cfg = configuracion.cargar()
    if not modelo_equipo.revisar(cfg)["clasificador"]["listo"]:
        pytest.skip("RosaNet no está lista")
    foto = sorted(glob.glob(str(configuracion.ruta("../app-tablet/assets/rosas/2_optimo/*.jpg"))))[0]
    with Image.open(foto) as im:
        rgb = np.asarray(im.convert("RGB"))
    clf = ClasificadorRosaNet(modelo_equipo.cargar(cfg, "clasificador"), cfg["percepcion"]["margen_recorte"])
    alto, ancho = rgb.shape[:2]
    res = clf.clasificar(captura(rgb), [Candidata((0, 0, ancho, alto))])[0]
    assert res["clase"] in {"inmaduro", "optimo", "pasado"}
    assert set(res["probs"]) == {"inmaduro", "optimo", "pasado"}
    assert res["seguro"] == (res["confianza"] >= modelo_equipo.umbral_seguro(cfg))


def test_carteles_miran_a_la_camara():
    mujoco = pytest.importorskip("mujoco")
    from sim.escena_invernadero import armar_escena
    from sim.rosas import ids_carteles, mirar_a_la_camara
    cfg = configuracion.cargar(cambios={"sim.rosas": "cartel"})
    escena = armar_escena(cfg)
    ids = ids_carteles(escena.m)
    assert len(ids) == len(escena.verdad)
    assert {r.estado for r in escena.verdad} <= {"inmaduro", "optimo", "pasado"}
    assert not any(r.lista_manana for r in escena.verdad)   # una foto no puede mostrar "lista mañana"
    camara = np.array([2.0, escena.plano.camino(1).y, 1.2])
    mirar_a_la_camara(escena.m, escena.d, ids, camara)
    for g in ids[:20]:
        cara = escena.d.geom_xmat[g].reshape(3, 3)[:, 2]
        hacia_camara = camara - escena.d.geom_xpos[g]
        assert np.dot(cara, hacia_camara / np.linalg.norm(hacia_camara)) == pytest.approx(1.0, abs=1e-6)
        assert escena.d.geom_xmat[g].reshape(3, 3)[2, 0] == pytest.approx(0.0, abs=1e-6)   # foto derecha


def test_el_detector_mira_la_foto_sin_achicarla():
    class DetectorConTamano:
        imgsz = 960
        def detect(self, img):
            return []
    det = DetectorConTamano()
    nativo = CandidatasDetector(det, tamano_nativo=True)
    nativo.buscar(captura(np.zeros((1080, 1920, 3), np.uint8)))
    assert det.imgsz == 1920                       # foto de la ronda: sin achicar
    nativo.buscar(captura(np.zeros((720, 1270, 3), np.uint8)))
    assert det.imgsz == 1280                       # redondeado a múltiplo de 32
    nativo.buscar(captura(np.zeros((480, 640, 3), np.uint8)))
    assert det.imgsz == 960                        # foto chica (webcam): igual que antes
    det.imgsz = 960
    CandidatasDetector(det).buscar(captura(np.zeros((1080, 1920, 3), np.uint8)))
    assert det.imgsz == 960                        # apagado: el tamaño del equipo
