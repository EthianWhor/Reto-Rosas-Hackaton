"""Pruebas del paso 5: bandeja de salida, reintentos y WiFi simulado."""

import json

import pytest

import configuracion
from reporte import envio


class Reloj:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


class EnviadorQueFalla:
    def __init__(self, fallas: int):
        self.fallas = fallas
        self.llamadas = 0

    def enviar(self, archivo):
        self.llamadas += 1
        if self.llamadas <= self.fallas:
            raise OSError("se cayó la red")


@pytest.fixture
def base(tmp_path):
    (tmp_path / "salida").mkdir()
    for nombre in ("reporte_INV1_2026-10-24.xlsx", "reporte_INV1_2026-10-24.json"):
        (tmp_path / "salida" / nombre).write_text(f"contenido de {nombre}", encoding="utf-8")
    return tmp_path


def test_sin_wifi_no_borra_nada_ni_cuenta_intentos(base):
    bandeja = envio.Bandeja(base)
    destino = base / "dashboard"
    destino.mkdir()
    r = bandeja.intentar(envio.EnviadorCarpeta(destino), envio.ConexionSimulada(False))
    assert r["sin_conexion"] and len(r["esperando"]) == 2
    assert len(bandeja.pendientes()) == 2 and not any(destino.iterdir())
    assert not bandeja.archivo_pendientes.exists()


def test_con_wifi_copia_y_mueve_a_enviados(base):
    bandeja = envio.Bandeja(base)
    destino = base / "dashboard"
    destino.mkdir()
    r = bandeja.intentar(envio.EnviadorCarpeta(destino), envio.ConexionSimulada(True))
    assert len(r["enviados"]) == 2 and bandeja.pendientes() == []
    assert sorted(p.name for p in destino.iterdir()) == sorted(p.name for p in (base / "enviados").iterdir())
    assert (destino / "reporte_INV1_2026-10-24.json").read_text(encoding="utf-8") == \
        "contenido de reporte_INV1_2026-10-24.json"


def test_enviar_dos_veces_lo_mismo_no_duplica(base):
    destino = base / "dashboard"
    destino.mkdir()
    archivo = base / "salida" / "reporte_INV1_2026-10-24.json"
    enviador = envio.EnviadorCarpeta(destino)
    enviador.enviar(archivo)
    enviador.enviar(archivo)
    assert [p.name for p in destino.iterdir()] == [archivo.name]


def test_reintentos_esperan_1_2_4_minutos(base):
    reloj = Reloj()
    bandeja = envio.Bandeja(base, espera_max_min=60, reloj=reloj)
    for p in bandeja.pendientes()[1:]:
        p.unlink()                       # un solo archivo para seguir la cuenta fácil
    enviador = EnviadorQueFalla(fallas=3)
    wifi = envio.ConexionSimulada(True)

    assert bandeja.intentar(enviador, wifi)["fallidos"]
    estado = json.loads(bandeja.archivo_pendientes.read_text(encoding="utf-8"))
    (nombre, e), = estado.items()
    assert e["intentos"] == 1 and e["proximo_intento"] == reloj.t + 60 and "red" in e["ultimo_error"]

    reloj.t += 30                         # todavía no toca
    assert bandeja.intentar(enviador, wifi)["esperando"] == [nombre] and enviador.llamadas == 1
    reloj.t += 30
    bandeja.intentar(enviador, wifi)      # 2.ª falla → espera 2 min
    e = json.loads(bandeja.archivo_pendientes.read_text(encoding="utf-8"))[nombre]
    assert e["proximo_intento"] == reloj.t + 120
    reloj.t += 120
    bandeja.intentar(enviador, wifi)      # 3.ª falla → espera 4 min
    assert json.loads(bandeja.archivo_pendientes.read_text(encoding="utf-8"))[nombre]["proximo_intento"] == reloj.t + 240
    reloj.t += 240
    assert bandeja.intentar(enviador, wifi)["enviados"] == [nombre]
    assert json.loads(bandeja.archivo_pendientes.read_text(encoding="utf-8")) == {}
    assert bandeja.pendientes() == []


def test_espera_maxima(base):
    reloj = Reloj()
    bandeja = envio.Bandeja(base, espera_max_min=5, reloj=reloj)
    enviador = EnviadorQueFalla(fallas=100)
    for _ in range(6):
        bandeja.intentar(enviador, envio.ConexionSimulada(True))
        reloj.t += 3600
    e = next(iter(json.loads(bandeja.archivo_pendientes.read_text(encoding="utf-8")).values()))
    assert e["proximo_intento"] - (reloj.t - 3600) == 300


def test_conexion_carpeta(tmp_path):
    assert envio.ConexionCarpeta(tmp_path).hay()
    assert not envio.ConexionCarpeta(tmp_path / "no_montada").hay()


def test_api(base, monkeypatch):
    import requests
    respuestas = iter([500, 201])
    enviados = []

    class Respuesta:
        def __init__(self, codigo):
            self.status_code = codigo

    def post(url, files, data, headers, timeout):
        enviados.append((url, data["nombre"], headers))
        return Respuesta(next(respuestas))

    monkeypatch.setattr(requests, "post", post)
    enviador = envio.EnviadorApi("https://dashboard.test/recibir", token="clave")
    archivo = base / "salida" / "reporte_INV1_2026-10-24.json"
    with pytest.raises(OSError):
        enviador.enviar(archivo)
    enviador.enviar(archivo)
    assert enviados[-1] == ("https://dashboard.test/recibir", archivo.name, {"Authorization": "Bearer clave"})


def test_crear_desde_config_en_sim(tmp_path, monkeypatch):
    monkeypatch.delenv("ENVIO_CARPETA", raising=False)
    cfg = configuracion.cargar()
    cfg["datos_dir"] = str(tmp_path)
    cfg["envio"]["carpeta_destino"] = str(tmp_path / "dashboard")
    wifi = envio.ConexionSimulada(False)
    bandeja, enviador, conexion = envio.crear(cfg, wifi)
    assert isinstance(enviador, envio.EnviadorCarpeta) and not conexion.hay()
    wifi.hay_wifi = True
    assert conexion.hay()
