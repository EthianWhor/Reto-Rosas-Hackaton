"""Envío de los reportes al dashboard sin WiFi constante (sección 11 del plan).

    datos/
    ├── salida/          ← reportes listos para enviar (.xlsx + .json)
    ├── enviados/        ← se mueven aquí cuando el dashboard confirma que llegó
    └── pendientes.json  ← intentos fallidos y cuándo se vuelve a probar

Cada `revisar_cada_s`:
    ¿hay conexión con el dashboard?  no → sigue esperando (no cuenta como intento)
                                     sí → envía cada archivo de salida/
                                          ¿llegó? sí → a enviados/
                                                  no → reintenta en 1, 2, 4, 8… min (hasta `espera_max_min`)

Nada se borra hasta que el dashboard confirma. Si un archivo se envía dos
veces, el dashboard lo reconoce por el nombre (lleva el id de la ronda).

Formas de enviar (`envio.metodo`, acordar con la persona del dashboard):
- carpeta: copia a una carpeta compartida (Drive / OneDrive sincronizado). Llegó = la copia quedó igual.
- api: POST del archivo a la dirección del dashboard. Llegó = responde 200/201 (o 409, ya lo tenía).
- supabase: sube el .json a la tabla `reportes` de Supabase con `subir()` de subir_reporte.py
  (del equipo de la app). Es de donde lo lee la app de la tablet. El Excel se queda en el robot.
- correo: todavía no está hecho.

La dirección, la carpeta y la clave van en robot/.env (está en git porque el repo es privado; ver .env.ejemplo).
En simulación, el WiFi "aparece" cuando el robot vuelve a la base.

Para dejarlo vigilando en el robot real:
    python -m reporte.envio            # revisa cada envio.revisar_cada_s hasta que se cierre
    python -m reporte.envio --una-vez  # un solo intento
"""

import argparse
import filecmp
import json
import os
import shutil
import time
from pathlib import Path

import configuracion

EXTENSIONES = (".xlsx", ".json")


# ---------- conexión ----------
class ConexionSimulada:
    """WiFi de la simulación: apagado durante la ronda, se prende al volver a la base."""

    def __init__(self, hay_wifi: bool = False):
        self.hay_wifi = hay_wifi

    def hay(self) -> bool:
        return self.hay_wifi


class ConexionCarpeta:
    """Hay conexión si la carpeta compartida existe (está montada / sincronizada)."""

    def __init__(self, destino: Path):
        self.destino = destino

    def hay(self) -> bool:
        return self.destino.is_dir()


class ConexionApi:
    """Hay conexión si el dashboard responde a un "ping" (cualquier respuesta HTTP)."""

    def __init__(self, url: str, timeout_s: float = 3.0):
        self.url, self.timeout = url, timeout_s

    def hay(self) -> bool:
        import requests
        try:
            requests.get(self.url, timeout=self.timeout)
            return True
        except requests.RequestException:
            return False


# ---------- formas de enviar ----------
class EnviadorCarpeta:
    def __init__(self, destino: Path):
        self.destino = destino

    def enviar(self, archivo: Path) -> None:
        """Copia con nombre temporal y luego renombra: el dashboard nunca ve un archivo a medias."""
        final = self.destino / archivo.name
        if final.exists() and filecmp.cmp(archivo, final, shallow=False):
            return  # ya estaba (envío repetido): cuenta como recibido
        temporal = self.destino / f".{archivo.name}.subiendo"
        shutil.copyfile(archivo, temporal)
        os.replace(temporal, final)
        if not filecmp.cmp(archivo, final, shallow=False):
            raise OSError("la copia no quedó igual")


class EnviadorSupabase:
    """Sube el reporte JSON a Supabase (tabla `reportes`), de donde lo lee la app de la tablet.

    Usa `subir()` de robot/subir_reporte.py, que es del equipo de la app: no se
    cambia aquí. Solo sube el .json; el Excel se queda en el robot, en salida/.
    Si ese id_ronda ya estaba, Supabase lo reemplaza (no duplica).
    Con `fotos` (un reporte.fotos.Storage), antes sube los recortes de las dudosas
    y pone su dirección web en `foto` (el archivo de salida/ no se cambia).
    """

    extensiones = (".json",)

    def __init__(self, url: str, clave: str, fotos=None):
        self.url, self.clave, self.fotos = url, clave, fotos

    def enviar(self, archivo: Path) -> None:
        from subir_reporte import subir
        reporte = json.loads(archivo.read_text(encoding="utf-8"))
        if self.fotos is not None:
            from reporte.fotos import poner_fotos
            # salida/reporte.json → rondas/<id_ronda>/ (ahí están las fotos y las cajas)
            reporte = poner_fotos(reporte, archivo.parent.parent / "rondas" / reporte["id_ronda"], self.fotos)
        subir(reporte, self.url, self.clave)


class EnviadorApi:
    def __init__(self, url: str, token: str | None = None, timeout_s: float = 30.0):
        self.url, self.token, self.timeout = url, token, timeout_s

    def enviar(self, archivo: Path) -> None:
        import requests
        cabeceras = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        with open(archivo, "rb") as f:
            r = requests.post(self.url, files={"archivo": (archivo.name, f)},
                              data={"nombre": archivo.name}, headers=cabeceras, timeout=self.timeout)
        if r.status_code not in (200, 201, 409):   # 409 = ya lo tenía
            raise OSError(f"el dashboard respondió {r.status_code}")


# ---------- bandeja ----------
class Bandeja:
    def __init__(self, base: Path, espera_max_min: float = 60, reloj=time.time):
        self.salida = base / "salida"
        self.enviados = base / "enviados"
        self.archivo_pendientes = base / "pendientes.json"
        self.espera_max_s = espera_max_min * 60
        self.reloj = reloj
        self.salida.mkdir(parents=True, exist_ok=True)
        self.enviados.mkdir(parents=True, exist_ok=True)

    def _leer(self) -> dict:
        if self.archivo_pendientes.exists():
            return json.loads(self.archivo_pendientes.read_text(encoding="utf-8"))
        return {}

    def _escribir(self, estado: dict) -> None:
        temporal = self.archivo_pendientes.with_suffix(".tmp")
        temporal.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(temporal, self.archivo_pendientes)

    def pendientes(self, extensiones=EXTENSIONES) -> list[Path]:
        return sorted(p for p in self.salida.iterdir() if p.suffix in extensiones)

    def intentar(self, enviador, conexion) -> dict:
        """Un intento sobre toda la bandeja. Devuelve {"enviados": [...], "fallidos": [...], "esperando": [...]}."""
        resumen = {"enviados": [], "fallidos": [], "esperando": [], "sin_conexion": False}
        archivos = self.pendientes(getattr(enviador, "extensiones", EXTENSIONES))   # supabase: solo .json
        if not archivos:
            return resumen
        if not conexion.hay():
            resumen["sin_conexion"] = True
            resumen["esperando"] = [p.name for p in archivos]
            return resumen
        estado = self._leer()
        ahora = self.reloj()
        for archivo in archivos:
            e = estado.get(archivo.name, {"intentos": 0, "proximo_intento": 0})
            if e["proximo_intento"] > ahora:
                resumen["esperando"].append(archivo.name)
                continue
            try:
                enviador.enviar(archivo)
            except Exception as error:   # cualquier falla: se reintenta más tarde, nunca se cae
                e["intentos"] += 1
                e["proximo_intento"] = ahora + min(60 * 2 ** (e["intentos"] - 1), self.espera_max_s)
                e["ultimo_error"] = str(error)
                estado[archivo.name] = e
                resumen["fallidos"].append(archivo.name)
                continue
            os.replace(archivo, self.enviados / archivo.name)
            estado.pop(archivo.name, None)
            resumen["enviados"].append(archivo.name)
        self._escribir(estado)
        return resumen


def crear(cfg: dict, conexion_sim: ConexionSimulada | None = None):
    """(bandeja, enviador, conexion) según el config y robot/.env."""
    from dotenv import load_dotenv
    load_dotenv(configuracion.RAIZ / ".env")
    env = cfg["envio"]
    base = configuracion.ruta(cfg["datos_dir"])
    bandeja = Bandeja(base, env["espera_max_min"])
    metodo = env["metodo"]
    if metodo == "carpeta":
        destino = configuracion.ruta(os.getenv("ENVIO_CARPETA") or env["carpeta_destino"])
        if cfg["modo"] == "sim":
            destino.mkdir(parents=True, exist_ok=True)   # la "carpeta del dashboard" simulada
        enviador, conexion = EnviadorCarpeta(destino), ConexionCarpeta(destino)
    elif metodo == "api":
        url = os.getenv("ENVIO_URL")
        if not url:
            raise RuntimeError("envio.metodo = api, pero falta ENVIO_URL en robot/.env")
        enviador = EnviadorApi(url, os.getenv("ENVIO_TOKEN"))
        conexion = ConexionApi(os.getenv("ENVIO_PING_URL") or url)
    elif metodo == "supabase":
        url, clave = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not clave:
            raise RuntimeError("envio.metodo = supabase, pero faltan SUPABASE_URL y "
                               "SUPABASE_SERVICE_ROLE_KEY en robot/.env (ver subir_reporte.py)")
        from reporte.fotos import BUCKET, Storage
        bucket = env.get("fotos_bucket", BUCKET)   # null en el config = sin fotos de dudosas
        enviador = EnviadorSupabase(url, clave, Storage(url, clave, bucket) if bucket else None)
        conexion = ConexionApi(f"{url.rstrip('/')}/rest/v1/")
    else:
        raise NotImplementedError(f"envio.metodo = {metodo} todavía no está hecho (usar carpeta, api o supabase)")
    if cfg["modo"] == "sim" and conexion_sim is not None:
        conexion = _Ambas(conexion_sim, conexion)
    return bandeja, enviador, conexion


class _Ambas:
    """En simulación: hace falta el WiFi simulado y además que el destino responda."""

    def __init__(self, *conexiones):
        self.conexiones = conexiones

    def hay(self) -> bool:
        return all(c.hay() for c in self.conexiones)


def describir(resumen: dict) -> str:
    if not (resumen["enviados"] or resumen["fallidos"] or resumen["esperando"]):
        return "la bandeja de salida está vacía"
    if resumen["sin_conexion"]:
        return f"sin conexión: {len(resumen['esperando'])} archivo(s) esperan en la bandeja de salida"
    partes = [f"{len(resumen['enviados'])} enviado(s)"]
    if resumen["fallidos"]:
        partes.append(f"{len(resumen['fallidos'])} fallaron (se reintenta más tarde)")
    if resumen["esperando"]:
        partes.append(f"{len(resumen['esperando'])} esperando su próximo intento")
    return ", ".join(partes)


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="Envía los reportes de datos/salida/ al dashboard.")
    p.add_argument("--una-vez", action="store_true", help="Un solo intento y salir")
    p.add_argument("--config", type=Path, help="Otro archivo de configuración (p. ej. config/demo.yaml)")
    args = p.parse_args(argv)
    cfg = configuracion.cargar(args.config)
    bandeja, enviador, conexion = crear(cfg)
    while True:
        print(describir(bandeja.intentar(enviador, conexion)), flush=True)
        if args.una_vez:
            return
        time.sleep(cfg["envio"]["revisar_cada_s"])


if __name__ == "__main__":
    main()
