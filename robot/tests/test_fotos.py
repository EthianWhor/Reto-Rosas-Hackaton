"""Pruebas de las fotos de dudosas en Supabase Storage (reporte/fotos.py), sin red."""

import io
import json
import urllib.error
import urllib.request

import pytest
from PIL import Image

import configuracion
from reporte import envio, fotos

URL = "https://x.supabase.co"


class SupabaseFalso:
    """Reemplaza urlopen: guarda cada pedido y responde como Storage."""

    def __init__(self, bucket_ya_existe=False, falla_en=()):
        self.pedidos = []
        self.bucket_ya_existe, self.falla_en = bucket_ya_existe, falla_en

    def __call__(self, pedido, timeout=None):
        self.pedidos.append(pedido)
        url = pedido.full_url
        if url.endswith("/storage/v1/bucket") and self.bucket_ya_existe:
            raise urllib.error.HTTPError(url, 409, "Conflict", {},
                                         io.BytesIO(b'{"error":"Duplicate","message":"The resource already exists"}'))
        if any(f in url for f in self.falla_en):
            raise urllib.error.HTTPError(url, 500, "Error", {}, io.BytesIO(b"se cayo"))
        return io.BytesIO(b"{}")

    def subidas(self):
        return [p for p in self.pedidos if "/object/" in p.full_url]


@pytest.fixture
def ronda(tmp_path):
    """datos/ con una ronda: una foto con dos rosas y su detecciones.jsonl."""
    carpeta = tmp_path / "rondas" / "INV1_2026-10-24_220000"
    (carpeta / "fotos").mkdir(parents=True)
    Image.new("RGB", (1920, 1080), (30, 30, 30)).save(carpeta / "fotos" / "c01_p00_der_media.png")
    dets = [
        {"foto": "fotos/c01_p00_der_media.png", "bbox": [100, 200, 180, 290], "cama": 1, "tramo": 1,
         "metro": 0.33, "altura_m": 1.09},
        {"foto": "fotos/c01_p00_der_media.png", "bbox": [900, 400, 1100, 600], "cama": 1, "tramo": 1,
         "metro": 1.5, "altura_m": 1.4},
    ]
    (carpeta / "detecciones.jsonl").write_text("\n".join(json.dumps(d) for d in dets), encoding="utf-8")
    reporte = {
        "id_ronda": "INV1_2026-10-24_220000", "invernadero": "INV1", "fecha": "2026-10-24",
        "rosas_listas": [{"rosa_id": "INV1-C01-T1-1.50-1.40", "foto": "fotos/c01_p00_der_media.png"}],
        "dudosas": [
            {"rosa_id": "INV1-C01-T1-0.33-1.09", "foto": "fotos/c01_p00_der_media.png", "confianza": 0.53},
            {"rosa_id": "INV1-C01-T1-1.50-1.40", "foto": "fotos/c01_p00_der_media.png", "confianza": 0.5},
            {"rosa_id": "INV1-C01-T1-9.99-1.00", "foto": "https://ya.subida/rosa.jpg", "confianza": 0.4},
        ],
    }
    (tmp_path / "salida").mkdir()
    (tmp_path / "salida" / "reporte_INV1_2026-10-24.json").write_text(json.dumps(reporte), encoding="utf-8")
    return tmp_path, carpeta, reporte


def test_sube_el_recorte_y_pone_la_direccion_web(ronda, monkeypatch):
    _, carpeta, reporte = ronda
    falso = SupabaseFalso()
    monkeypatch.setattr(urllib.request, "urlopen", falso)
    nuevo = fotos.poner_fotos(reporte, carpeta, fotos.Storage(URL, "clave"))

    assert [d["foto"] for d in nuevo["dudosas"]] == [
        f"{URL}/storage/v1/object/public/fotos-rosas/INV1_2026-10-24_220000/INV1-C01-T1-0.33-1.09.jpg",
        f"{URL}/storage/v1/object/public/fotos-rosas/INV1_2026-10-24_220000/INV1-C01-T1-1.50-1.40.jpg",
        "https://ya.subida/rosa.jpg",   # ya era web: no se toca
    ]
    assert reporte["dudosas"][0]["foto"] == "fotos/c01_p00_der_media.png"   # el original no cambia
    assert nuevo["rosas_listas"] == reporte["rosas_listas"]

    crear = falso.pedidos[0]
    assert crear.full_url == f"{URL}/storage/v1/bucket" and json.loads(crear.data)["public"] is True
    assert len([p for p in falso.pedidos if p.full_url.endswith("/bucket")]) == 1   # el bucket, una sola vez
    sub = falso.subidas()[0]
    assert sub.get_method() == "POST" and sub.headers["X-upsert"] == "true"
    assert sub.headers["Authorization"] == "Bearer clave" and sub.headers["Content-type"] == "image/jpeg"
    # recorte de la caja 80 x 90 con 15 % de margen, agrandado a 256 px de lado mínimo
    img = Image.open(io.BytesIO(sub.data))
    assert min(img.size) == 256 and 1.0 < img.height / img.width < 1.25


def test_bucket_que_ya_existe_no_es_error(ronda, monkeypatch):
    _, carpeta, reporte = ronda
    falso = SupabaseFalso(bucket_ya_existe=True)
    monkeypatch.setattr(urllib.request, "urlopen", falso)
    nuevo = fotos.poner_fotos(reporte, carpeta, fotos.Storage(URL, "clave"))
    assert all(d["foto"].startswith("http") for d in nuevo["dudosas"])


def test_si_una_foto_falla_esa_queda_con_su_nombre(ronda, monkeypatch):
    _, carpeta, reporte = ronda
    monkeypatch.setattr(urllib.request, "urlopen", SupabaseFalso(falla_en=("0.33-1.09",)))
    nuevo = fotos.poner_fotos(reporte, carpeta, fotos.Storage(URL, "clave"))
    assert nuevo["dudosas"][0]["foto"] == "fotos/c01_p00_der_media.png"
    assert nuevo["dudosas"][1]["foto"].startswith("https://")


def test_sin_bucket_el_reporte_sale_igual(ronda, monkeypatch):
    _, carpeta, reporte = ronda
    falso = SupabaseFalso(falla_en=("/bucket",))
    monkeypatch.setattr(urllib.request, "urlopen", falso)
    assert fotos.poner_fotos(reporte, carpeta, fotos.Storage(URL, "clave")) == reporte
    assert len(falso.pedidos) == 1   # no intenta foto por foto


def test_foto_que_no_existe_no_frena(ronda, monkeypatch):
    _, carpeta, reporte = ronda
    (carpeta / "fotos" / "c01_p00_der_media.png").unlink()
    monkeypatch.setattr(urllib.request, "urlopen", SupabaseFalso())
    nuevo = fotos.poner_fotos(reporte, carpeta, fotos.Storage(URL, "clave"))
    assert [d["foto"] for d in nuevo["dudosas"]] == [d["foto"] for d in reporte["dudosas"]]


def test_sin_caja_sube_la_foto_entera(ronda, monkeypatch):
    _, carpeta, reporte = ronda
    (carpeta / "detecciones.jsonl").unlink()
    falso = SupabaseFalso()
    monkeypatch.setattr(urllib.request, "urlopen", falso)
    fotos.poner_fotos(reporte, carpeta, fotos.Storage(URL, "clave"))
    assert Image.open(io.BytesIO(falso.subidas()[0].data)).size == (1920, 1080)


def test_enviador_supabase_sube_el_reporte_con_las_fotos(ronda, monkeypatch):
    import subir_reporte
    base, _, _ = ronda
    monkeypatch.setattr(urllib.request, "urlopen", SupabaseFalso())
    subidos = []
    monkeypatch.setattr(subir_reporte, "subir", lambda rep, url, clave: subidos.append(rep))
    archivo = base / "salida" / "reporte_INV1_2026-10-24.json"
    antes = archivo.read_text(encoding="utf-8")
    r = envio.Bandeja(base).intentar(envio.EnviadorSupabase(URL, "clave", fotos.Storage(URL, "clave")),
                                     envio.ConexionSimulada(True))
    assert r["enviados"] == ["reporte_INV1_2026-10-24.json"]
    assert subidos[0]["dudosas"][0]["foto"].startswith(f"{URL}/storage/v1/object/public/")
    assert (base / "enviados" / archivo.name).read_text(encoding="utf-8") == antes   # el archivo no se cambia


def test_config_demo(monkeypatch, tmp_path):
    cfg = configuracion.cargar(configuracion.RAIZ / "config" / "demo.yaml")
    assert cfg["sim"]["rosas"] == "cartel" and cfg["envio"]["metodo"] == "supabase"
    monkeypatch.setenv("SUPABASE_URL", URL)
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "clave")
    cfg["datos_dir"] = str(tmp_path)
    _, enviador, _ = envio.crear(cfg)
    assert isinstance(enviador, envio.EnviadorSupabase) and enviador.fotos.bucket == "fotos-rosas"
    # el resto de demo.yaml es igual a config.yaml
    base = configuracion.cargar()
    for clave in ("sim.rosas", "envio.metodo", "envio.fotos_bucket"):
        for c in (cfg, base):
            *camino, ultima = clave.split(".")
            nodo = c
            for parte in camino:
                nodo = nodo[parte]
            nodo.pop(ultima, None)
    cfg["datos_dir"] = base["datos_dir"]
    assert cfg == base
