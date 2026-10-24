"""Puente entre el AgiBot X2 Ultra y el PC de la demo (se corre EN EL ROBOT).

El robot ya trae ROS 2 Humble y el SDK AimDK_X2; el modelo (detector + RosaNet) corre en el PC.
Este script es lo único que va en el robot: lee la cámara de la cabeza y prende la tira LED del
pecho cuando el PC se lo pide. Solo usa ROS 2 y la librería estándar de Python (no hay que
instalar nada en el robot). El robot queda quieto: no camina ni mueve la cintura.

En el robot (con el entorno de ROS 2 y del SDK cargado, como para los ejemplos de AgiBot):
    python3 puente_x2.py                      # escucha en el puerto 8765
    python3 puente_x2.py --puerto 8765 --modo-led 2 --segundos-led 8

En el PC (desde robot/):
    python modo_foto.py --robot http://<ip-del-robot>:8765 --enviar --config config/demo.yaml

Lo que sirve por la red local:
    GET  /foto    la última imagen de la cámara (PNG; el formato de ROS va en la cabecera X-Encoding)
    GET  /estado  si llegan imágenes, de qué tamaño, y los campos del pedido del LED (para ajustarlo)
    POST /led     {"encender": true}: parpadea la tira LED `--segundos-led` segundos y se apaga sola

Nombres sacados de la documentación AimDK_X2 1.1.0 (ver cuerpo/real_backend.py). Si el LED no
responde, mirar /estado: muestra los campos que pide SetPmuLed en este firmware, y se ajustan con
--modo-led / --modo-apagado o --campo-led nombre=valor.
"""

import argparse
import json
import struct
import threading
import time
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOPICO_RGB = "/aima/hal/sensor/rgbd_head_front/rgb_image"   # sensor_msgs/Image 1280 × 720, 30 Hz
SRV_LED = "/aimdk_5Fmsgs/srv/SetPmuLed"                     # tira LED del pecho (tarda ~5 s en responder)
CANALES = {"rgb8": 3, "bgr8": 3, "rgba8": 4, "bgra8": 4, "mono8": 1}


def png(ancho: int, alto: int, canales: int, datos: bytes, paso: int) -> bytes:
    """PNG sin compresión pesada, solo con zlib (para no depender de PIL ni OpenCV en el robot)."""
    tipo = {1: 0, 3: 2, 4: 6}[canales]
    fila = ancho * canales
    crudo = b"".join(b"\x00" + datos[y * paso:y * paso + fila] for y in range(alto))

    def bloque(nombre: bytes, contenido: bytes) -> bytes:
        return (struct.pack(">I", len(contenido)) + nombre + contenido
                + struct.pack(">I", zlib.crc32(nombre + contenido) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n" + bloque(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, tipo, 0, 0, 0))
            + bloque(b"IDAT", zlib.compress(crudo, 1)) + bloque(b"IEND", b""))


class Estado:
    """Lo último que llegó de la cámara y lo que pasó con el LED (compartido entre hilos)."""

    def __init__(self):
        self.lock = threading.Lock()
        self.imagen = None          # (ancho, alto, encoding, paso, datos, hora)
        self.led = {"ultimo_pedido": None, "respuesta": None, "error": None}
        self.campos_led = None

    def guardar_imagen(self, ancho, alto, encoding, paso, datos):
        with self.lock:
            self.imagen = (ancho, alto, encoding, paso, bytes(datos), time.time())

    def foto_png(self):
        with self.lock:
            imagen = self.imagen
        if imagen is None:
            return None
        ancho, alto, encoding, paso, datos, hora = imagen
        if encoding not in CANALES:
            raise ValueError(f"formato de imagen no soportado: {encoding}")
        return png(ancho, alto, CANALES[encoding], datos, paso), encoding, time.time() - hora

    def resumen(self) -> dict:
        with self.lock:
            img = self.imagen
            return {"imagen": None if img is None else {"ancho": img[0], "alto": img[1], "encoding": img[2],
                                                         "edad_s": round(time.time() - img[5], 2)},
                    "led": dict(self.led), "campos_led": self.campos_led}


def manejador(estado: Estado, pedir_led):
    class Manejador(BaseHTTPRequestHandler):
        def _responder(self, codigo, cuerpo: bytes, tipo="application/json", extra=None):
            self.send_response(codigo)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(cuerpo)))
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(cuerpo)

        def _json(self, codigo, datos):
            self._responder(codigo, json.dumps(datos, ensure_ascii=False).encode("utf-8"))

        def do_GET(self):
            if self.path == "/foto":
                try:
                    foto = estado.foto_png()
                except ValueError as e:
                    return self._json(500, {"error": str(e)})
                if foto is None:
                    return self._json(503, {"error": f"todavía no llegó ninguna imagen de {TOPICO_RGB}"})
                datos, encoding, edad = foto
                return self._responder(200, datos, "image/png", {"X-Encoding": encoding, "X-Edad-s": f"{edad:.2f}"})
            if self.path == "/estado":
                return self._json(200, estado.resumen())
            self._json(404, {"error": "use /foto, /estado o POST /led"})

        def do_POST(self):
            if self.path != "/led":
                return self._json(404, {"error": "use POST /led"})
            largo = int(self.headers.get("Content-Length") or 0)
            try:
                pedido = json.loads(self.rfile.read(largo) or b"{}")
            except json.JSONDecodeError:
                return self._json(400, {"error": "el cuerpo tiene que ser JSON"})
            pedir_led(bool(pedido.get("encender", True)))
            self._json(202, {"ok": True})

        def log_message(self, formato, *args):   # una línea corta por pedido
            print(f"{self.address_string()} {formato % args}", flush=True)

    return Manejador


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="Puente cámara + LED del X2 Ultra para el PC de la demo")
    p.add_argument("--puerto", type=int, default=8765)
    p.add_argument("--topico", default=TOPICO_RGB)
    p.add_argument("--servicio-led", default=SRV_LED)
    p.add_argument("--modo-led", type=int, default=2, help="led_strip_mode al encender (2 = parpadeo)")
    p.add_argument("--modo-apagado", type=int, default=0, help="led_strip_mode al apagar")
    p.add_argument("--segundos-led", type=float, default=8.0, help="cuánto parpadea antes de apagarse")
    p.add_argument("--campo-led", action="append", default=[], metavar="NOMBRE=VALOR",
                   help="otro campo del pedido SetPmuLed (p. ej. r=0 g=255 b=0), si el firmware lo pide")
    args = p.parse_args(argv)

    import rclpy
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import Image

    rclpy.init()
    nodo = rclpy.create_node("puente_rosas")
    estado = Estado()
    nodo.create_subscription(Image, args.topico, lambda m: estado.guardar_imagen(
        m.width, m.height, m.encoding, m.step, m.data), qos_profile_sensor_data)   # BEST_EFFORT, como pide el SDK

    try:
        from aimdk_msgs.srv import SetPmuLed
        cliente = nodo.create_client(SetPmuLed, args.servicio_led)
        estado.campos_led = SetPmuLed.Request.get_fields_and_field_types()
    except ImportError as e:
        cliente, SetPmuLed = None, None
        estado.led["error"] = f"sin aimdk_msgs: {e} (la cámara funciona igual)"
    print(f"Campos de SetPmuLed: {estado.campos_led}", flush=True)

    extras = {}
    for par in args.campo_led:
        nombre, valor = par.split("=", 1)
        extras[nombre] = int(valor) if valor.lstrip("-").isdigit() else valor
    apagar_en = {"t": None}

    def enviar_led(modo: int):
        if cliente is None:
            return
        req = SetPmuLed.Request()
        for nombre, valor in {"led_strip_mode": modo, **extras}.items():
            if hasattr(req, nombre):
                setattr(req, nombre, valor)
        estado.led["ultimo_pedido"] = {"led_strip_mode": modo, **extras, "hora": time.strftime("%H:%M:%S")}

        def listo(fut):
            try:
                estado.led["respuesta"], estado.led["error"] = str(fut.result()), None
            except Exception as e:   # noqa: BLE001  (se muestra en /estado)
                estado.led["error"] = repr(e)
        cliente.call_async(req).add_done_callback(listo)

    def pedir_led(encender: bool):
        if encender:
            apagar_en["t"] = time.time() + args.segundos_led
            enviar_led(args.modo_led)
        else:
            apagar_en["t"] = None
            enviar_led(args.modo_apagado)

    def reloj():   # apaga el LED cuando pasa el tiempo
        if apagar_en["t"] is not None and time.time() >= apagar_en["t"]:
            apagar_en["t"] = None
            enviar_led(args.modo_apagado)
    nodo.create_timer(0.5, reloj)

    threading.Thread(target=rclpy.spin, args=(nodo,), daemon=True).start()
    servidor = ThreadingHTTPServer(("0.0.0.0", args.puerto), manejador(estado, pedir_led))
    print(f"Puente listo en el puerto {args.puerto}: cámara {args.topico}, LED {args.servicio_led}", flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        enviar_led(args.modo_apagado)
        time.sleep(0.5)
        nodo.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
