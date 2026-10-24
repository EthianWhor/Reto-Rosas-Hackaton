"""Modo foto (demo en vivo): una foto pasa por el mismo pipeline del robot."""

import glob
import json

import numpy as np
import pytest
from PIL import Image

import configuracion
import modo_foto
from percepcion import modelo_equipo
from reporte.tabla import COLUMNAS_CUADRANTES


@pytest.fixture(scope="module")
def cfg():
    return configuracion.cargar()


def rosa(estado, caja=(10, 10, 60, 60), conf=0.8, completa=False):
    return modo_foto.RosaFoto(list(caja), estado, estado if estado != "dudosa" else "optimo", conf,
                              {"inmaduro": 0.1, "optimo": conf, "pasado": 0.1}, {"mirar": ["algo"]}, completa)


def test_dibujar_agranda_las_fotos_pequenas_y_pinta_por_estado():
    rgb = np.zeros((200, 300, 3), np.uint8)
    img = modo_foto.dibujar(rgb, [rosa("optimo"), rosa("inmaduro", (100, 100, 150, 150))])
    assert img.width == modo_foto.ANCHO_MIN_DIBUJO
    escala = img.width / 300
    borde = img.getpixel((round(10 * escala), round(35 * escala)))
    assert borde == modo_foto.COLORES["optimo"]


def test_explicar_y_resumen():
    rosas = [rosa("optimo"), rosa("dudosa", conf=0.52)]
    texto = modo_foto.explicar(rosas)
    assert "Rosa 1: Óptimo" in texto and "Rosa 2: Dudosa" in texto and "revise alguien" in texto
    assert modo_foto.resumen(rosas) == {"optimo": 1, "inmaduro": 0, "pasado": 0, "dudosa": 1}
    assert "analicé la rosa de cerca" in modo_foto.explicar([rosa("inmaduro", completa=True)])
    assert modo_foto.explicar([]) == "No encontré rosas en la foto."
    assert modo_foto.explicar([], "La cámara no muestra imagen") == "La cámara no muestra imagen"


def test_cuadro_guia_centrado():
    x1, y1, x2, y2 = modo_foto.cuadro_guia(640, 480)
    assert x2 - x1 == y2 - y1 == int(modo_foto.GUIA_FRAC * 480)
    assert (x1 + x2) // 2 == 320 and (y1 + y2) // 2 == 240


def test_camara_tapada_o_cuadro_vacio_no_inventa_rosas(cfg):
    if not all(e["listo"] for e in modelo_equipo.revisar(cfg).values()):
        pytest.skip("el modelo del equipo no está listo")
    an = modo_foto.Analizador(cfg)
    gris = np.full((480, 640, 3), 140, np.uint8)            # lo que entrega Windows con la cámara tapada
    assert an.analizar(gris, modo_foto.cuadro_guia(640, 480)) == [] and "no muestra imagen" in an.motivo
    sin_rosa = np.zeros((480, 640, 3), np.uint8)
    sin_rosa[:, :320] = (40, 90, 160)                       # una pared azul y negro: nada rojizo
    assert an.analizar(sin_rosa, modo_foto.cuadro_guia(640, 480)) == [] and "dentro del cuadro" in an.motivo


def test_con_la_camara_analiza_solo_el_cuadro_guia(cfg):
    if not all(e["listo"] for e in modelo_equipo.revisar(cfg).values()):
        pytest.skip("el modelo del equipo no está listo")
    an = modo_foto.Analizador(cfg)
    foto = sorted(glob.glob(str(configuracion.ruta("../app-tablet/assets/rosas/2_optimo/*.jpg"))))[0]
    with Image.open(foto) as im:
        rosa_img = np.asarray(im.convert("RGB").resize((240, 240)))
    cuadro = np.zeros((480, 640, 3), np.uint8)
    cuadro[:] = (60, 60, 60)
    guia = modo_foto.cuadro_guia(640, 480)
    cuadro[120:360, 200:440] = rosa_img                       # la rosa dentro del cuadro guía
    rosas = an.analizar(cuadro, guia)
    assert len(rosas) == 1 and rosas[0].caja == list(guia) and rosas[0].foto_completa


def test_mini_reporte_tiene_el_formato_que_lee_la_app(cfg):
    rep = modo_foto.mini_reporte([rosa("optimo"), rosa("inmaduro"), rosa("dudosa", conf=0.5)], cfg, "x.jpg")
    assert rep.id_ronda.startswith("INV1_DEMO_")
    assert list(rep.cuadrantes[0]) == COLUMNAS_CUADRANTES        # app-tablet/src/data/reporte.ts
    assert (rep.cuadrantes[0]["optimo"], rep.cuadrantes[0]["total"]) == (1, 3)
    assert [r["estado"] for r in rep.rosas_listas] == ["optimo"] and len(rep.dudosas) == 1


def test_foto_real_de_la_finca_con_el_modelo_del_equipo(cfg, tmp_path):
    if not all(e["listo"] for e in modelo_equipo.revisar(cfg).values()):
        pytest.skip("el modelo del equipo no está listo")
    analizador = modo_foto.Analizador(cfg)
    assert analizador.eleccion == {"candidatas": "detector_equipo", "clasificador": "rosanet", "notas": []}
    foto = sorted(glob.glob(str(configuracion.ruta("../app-tablet/assets/rosas/2_optimo/*.jpg"))))[0]
    with Image.open(foto) as im:
        rgb = np.asarray(im.convert("RGB"))
    rosas = modo_foto.procesar(rgb, "rosa.jpg", analizador, tmp_path, cfg)
    assert len(rosas) >= 1 and all(r.estado in {"optimo", "inmaduro", "pasado", "dudosa"} for r in rosas)
    assert (tmp_path / "rosa_anotada.jpg").exists()
    guardado = json.loads((tmp_path / "rosa.json").read_text(encoding="utf-8"))
    assert guardado["conteo"] == modo_foto.resumen(rosas)
