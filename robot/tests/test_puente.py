"""Puente con el X2 real (puente_x2.py) y la cámara del robot en el modo foto, sin ROS ni robot."""

import io
import threading
from http.server import ThreadingHTTPServer

import numpy as np
import pytest
from PIL import Image

import modo_foto
import puente_x2


def test_png_sin_librerias_con_relleno_por_fila():
    ancho, alto = 5, 3
    img = np.arange(alto * ancho * 3, dtype=np.uint8).reshape(alto, ancho, 3)
    paso = ancho * 3 + 4                          # ROS puede traer bytes de relleno al final de cada fila
    datos = b"".join(fila.tobytes() + b"\xff" * 4 for fila in img)
    with Image.open(io.BytesIO(puente_x2.png(ancho, alto, 3, datos, paso))) as im:
        assert np.array_equal(np.asarray(im), img)


@pytest.fixture
def puente():
    """El servidor del puente en este PC, con una imagen falsa en vez de la cámara de ROS."""
    estado = puente_x2.Estado()
    pedidos = []
    servidor = ThreadingHTTPServer(("127.0.0.1", 0), puente_x2.manejador(estado, pedidos.append))
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    yield estado, pedidos, f"http://127.0.0.1:{servidor.server_address[1]}"
    servidor.shutdown()


def test_la_camara_del_robot_llega_en_bgr_como_opencv(puente):
    estado, _, url = puente
    cam = modo_foto.CamaraRobot(url)
    assert cam.isOpened() and cam.read() == (False, None)      # el puente corre pero todavía no hay imagen
    rojo = np.zeros((4, 6, 3), np.uint8)
    rojo[..., 0] = 200                                          # rojo en RGB
    estado.guardar_imagen(6, 4, "rgb8", 18, rojo.tobytes())
    ok, cuadro = cam.read()
    assert ok and cuadro.shape == (4, 6, 3) and tuple(cuadro[0, 0]) == (0, 0, 200)   # BGR
    estado.guardar_imagen(6, 4, "bgr8", 18, rojo[..., ::-1].copy().tobytes())        # la cámara manda BGR
    ok, cuadro = cam.read()
    assert ok and tuple(cuadro[0, 0]) == (0, 0, 200)


def test_led_y_estado(puente):
    estado, pedidos, url = puente
    cam = modo_foto.CamaraRobot(url)
    assert cam.prender_led() and cam.prender_led(False)
    assert pedidos == [True, False]
    estado.guardar_imagen(2, 2, "rgb8", 6, bytes(12))
    import json
    import urllib.request
    with urllib.request.urlopen(f"{url}/estado") as r:
        resumen = json.load(r)
    assert resumen["imagen"]["ancho"] == 2 and resumen["imagen"]["encoding"] == "rgb8"


def test_sin_puente_avisa_que_no_hay_camara():
    cam = modo_foto.CamaraRobot("http://127.0.0.1:9", espera_s=0.5)   # nadie escucha en ese puerto
    assert not cam.isOpened() and cam.read() == (False, None) and not cam.prender_led()
