"""Sube a Supabase el reporte JSON de una ronda del robot (tabla reportes, supabase/schema.sql).

La app de la tablet lee de ahí el último reporte para el turnero y el reparto del turno.

Uso (desde robot/):
    python subir_reporte.py datos/salida/reporte_INV1_2026-10-24.json

Necesita en robot/.env (no se sube al repo) o en variables de entorno:
    SUPABASE_URL=https://fxlljandvphujxxddvxy.supabase.co
    SUPABASE_SERVICE_ROLE_KEY=...   (Supabase → Project Settings → API; solo en el robot, nunca en la app)

Si el reporte de esa ronda ya estaba, lo reemplaza (mismo id_ronda). Devuelve 0 si llegó.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def _leer_env(ruta: Path) -> None:
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            clave, valor = linea.split("=", 1)
            os.environ.setdefault(clave.strip(), valor.strip())


def subir(reporte: dict, url: str, clave: str) -> None:
    fila = {
        "id_ronda": reporte["id_ronda"],
        "invernadero": reporte["invernadero"],
        "fecha": reporte["fecha"],
        "datos": reporte,
    }
    pedido = urllib.request.Request(
        f"{url.rstrip('/')}/rest/v1/reportes?on_conflict=id_ronda",
        data=json.dumps(fila).encode("utf-8"),
        method="POST",
        headers={
            "apikey": clave,
            "Authorization": f"Bearer {clave}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal",
        },
    )
    with urllib.request.urlopen(pedido, timeout=30) as respuesta:
        if respuesta.status not in (200, 201, 204):
            raise RuntimeError(f"Supabase respondió {respuesta.status}")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    _leer_env(Path(__file__).with_name(".env"))
    url, clave = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not clave:
        print("Faltan SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY (en robot/.env).")
        return 2
    reporte = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    try:
        subir(reporte, url, clave)
    except (urllib.error.URLError, RuntimeError) as e:
        detalle = e.read().decode("utf-8", "replace") if isinstance(e, urllib.error.HTTPError) else e
        print(f"No se pudo subir {reporte['id_ronda']}: {detalle}")
        return 1
    print(f"Reporte {reporte['id_ronda']} subido a Supabase.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
