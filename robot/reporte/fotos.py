"""Fotos de las rosas dudosas para la app (paso 5 de conectar-robot-con-app).

La app solo muestra la foto de una dudosa si `foto` es una dirección web. Antes de
subir el reporte a Supabase, esto recorta cada dudosa de su foto (con la caja que
guardó la ronda en detecciones.jsonl), sube el recorte a Supabase Storage (bucket
público) y pone esa dirección en `foto`.

Si algo falla con una foto, esa dudosa se queda con el nombre del archivo y la app
muestra la foto de muestra: el reporte se sube igual, nunca se frena por las fotos.
"""

import io
import json
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

BUCKET = "fotos-rosas"
MARGEN = 0.15        # el mismo margen_recorte de percepcion (robot/CLAUDE.md)
LADO_MIN_PX = 256    # los recortes chicos se agrandan para que se vean bien en la tablet


def _id_rosa(det: dict, invernadero: str) -> str:
    """El mismo rosa_id que arma percepcion/dedup.py con la mejor vista."""
    return f"{invernadero}-C{det['cama']:02d}-T{det['tramo']}-{det['metro']:.2f}-{det['altura_m']:.2f}"


def _cajas(carpeta_ronda: Path, invernadero: str) -> dict:
    """{(rosa_id, foto): bbox} con las detecciones de la ronda. El modo foto guarda el `rosa_id` en cada línea."""
    archivo = carpeta_ronda / "detecciones.jsonl"
    cajas = {}
    if not archivo.exists():
        return cajas
    for linea in archivo.read_text(encoding="utf-8").splitlines():
        if linea.strip():
            det = json.loads(linea)
            rosa_id = det.get("rosa_id") or _id_rosa(det, invernadero)
            cajas.setdefault((rosa_id, det["foto"]), det["bbox"])
    return cajas


def recortar(foto: Path, bbox) -> bytes:
    """JPEG del recorte de la rosa con margen; sin caja, la foto entera."""
    img = Image.open(foto).convert("RGB")
    if bbox:
        x1, y1, x2, y2 = bbox
        mx, my = (x2 - x1) * MARGEN, (y2 - y1) * MARGEN
        img = img.crop((max(0, x1 - mx), max(0, y1 - my), min(img.width, x2 + mx), min(img.height, y2 + my)))
    if min(img.size) < LADO_MIN_PX:
        escala = LADO_MIN_PX / min(img.size)
        img = img.resize((round(img.width * escala), round(img.height * escala)), Image.LANCZOS)
    salida = io.BytesIO()
    img.save(salida, "JPEG", quality=90)
    return salida.getvalue()


class Storage:
    """Lo mínimo de Supabase Storage: crear el bucket público y subir un archivo."""

    def __init__(self, url: str, clave: str, bucket: str = BUCKET):
        self.url, self.clave, self.bucket = url.rstrip("/"), clave, bucket
        self._bucket_listo = False

    def _pedir(self, ruta: str, datos: bytes, tipo: str, extra: dict | None = None) -> None:
        pedido = urllib.request.Request(f"{self.url}/storage/v1/{ruta}", data=datos, method="POST", headers={
            "apikey": self.clave, "Authorization": f"Bearer {self.clave}", "Content-Type": tipo, **(extra or {})})
        with urllib.request.urlopen(pedido, timeout=30):
            pass

    def crear_bucket(self) -> None:
        if self._bucket_listo:
            return
        datos = json.dumps({"id": self.bucket, "name": self.bucket, "public": True}).encode("utf-8")
        try:
            self._pedir("bucket", datos, "application/json")
        except urllib.error.HTTPError as e:
            if "exist" not in e.read().decode("utf-8", "replace").lower():   # ya estaba: está bien
                raise
        self._bucket_listo = True

    def subir(self, ruta: str, datos: bytes) -> str:
        """Sube (o reemplaza) el archivo y devuelve su dirección pública."""
        self.crear_bucket()
        self._pedir(f"object/{self.bucket}/{ruta}", datos, "image/jpeg", {"x-upsert": "true"})
        return f"{self.url}/storage/v1/object/public/{self.bucket}/{ruta}"


def poner_fotos(reporte: dict, carpeta_ronda: Path, storage: Storage) -> dict:
    """Copia del reporte con `foto` = dirección web en cada dudosa que se pudo subir."""
    dudosas = reporte.get("dudosas") or []
    pendientes = [d for d in dudosas if d.get("foto") and not str(d["foto"]).startswith("http")]
    if not pendientes:
        return reporte
    try:
        storage.crear_bucket()
    except Exception as error:   # sin bucket no se intenta foto por foto
        print(f"Fotos de dudosas: no se pudo preparar el bucket {storage.bucket} ({error}); "
              "el reporte se sube sin fotos", flush=True)
        return reporte
    cajas = _cajas(carpeta_ronda, reporte.get("invernadero", ""))
    nuevas, subidas, fallas = [], 0, []
    for d in dudosas:
        if d in pendientes:
            try:
                foto = carpeta_ronda / d["foto"]
                datos = recortar(foto, cajas.get((d["rosa_id"], d["foto"])))
                d = {**d, "foto": storage.subir(f"{reporte['id_ronda']}/{d['rosa_id']}.jpg", datos)}
                subidas += 1
            except Exception as error:   # cualquier falla: esa dudosa queda con la foto de muestra
                fallas.append(f"{d.get('rosa_id')}: {error}")
        nuevas.append(d)
    print(f"Fotos de dudosas: {subidas} subidas a Supabase Storage"
          + (f", {len(fallas)} sin foto (la app muestra la de muestra). Primera falla: {fallas[0]}" if fallas else ""),
          flush=True)
    return {**reporte, "dudosas": nuevas}
