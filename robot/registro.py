"""Log de cada ronda en archivo (sección 15 del plan).

Todo lo que el programa escribe en pantalla se copia, con la hora, a
`datos/logs/ronda_<id_ronda>.log`. Si se sigue una ronda interrumpida (`--continuar`), se
agrega al mismo archivo. Lo que se escribe antes de saber el id de la ronda (revisión del modelo)
se guarda en memoria y se vuelca al abrir el archivo. Si el programa se cae, el error completo
queda en el log (o en `datos/logs/error_<fecha>.log` si todavía no había ronda).
"""

import sys
import traceback
from datetime import datetime
from pathlib import Path

_activa = None


def abrir_log(ruta: Path) -> None:
    """Empieza a escribir el log de la ronda en `ruta` (si hay una bitácora activa)."""
    if _activa is not None:
        _activa.abrir(ruta)


class Bitacora:
    def __init__(self, carpeta_logs: Path):
        self.carpeta_logs = carpeta_logs
        self.pantalla = sys.stdout
        self.archivo = None
        self.pendiente: list[str] = []
        self.linea_nueva = True

    # --- se comporta como sys.stdout ---
    def write(self, texto: str) -> int:
        self.pantalla.write(texto)
        self._guardar(texto)
        return len(texto)

    def flush(self) -> None:
        self.pantalla.flush()
        if self.archivo:
            self.archivo.flush()

    def isatty(self) -> bool:
        return self.pantalla.isatty()

    @property
    def encoding(self) -> str:
        return self.pantalla.encoding

    def _guardar(self, texto: str) -> None:
        partes = []
        for linea in texto.splitlines(keepends=True):
            if self.linea_nueva:
                partes.append(f"{datetime.now():%Y-%m-%d %H:%M:%S}  ")
            partes.append(linea)
            self.linea_nueva = linea.endswith("\n")
        if self.archivo:
            self.archivo.write("".join(partes))
            self.archivo.flush()            # si se va la luz, lo escrito queda
        else:
            self.pendiente.extend(partes)

    def abrir(self, ruta: Path) -> None:
        if self.archivo:
            return
        ruta.parent.mkdir(parents=True, exist_ok=True)
        self.archivo = open(ruta, "a", encoding="utf-8")
        self.archivo.write("".join(self.pendiente))
        self.pendiente.clear()
        self.archivo.flush()
        self.ruta = ruta

    def __enter__(self) -> "Bitacora":
        global _activa
        _activa = self
        sys.stdout = self
        return self

    def __exit__(self, tipo, error, rastro) -> None:
        global _activa
        if tipo is not None and not issubclass(tipo, (SystemExit, KeyboardInterrupt)):
            if self.archivo is None:
                self.abrir(self.carpeta_logs / f"error_{datetime.now():%Y-%m-%d_%H%M%S}.log")
            self._guardar("ERROR:\n" + "".join(traceback.format_exception(tipo, error, rastro)))
        sys.stdout = self.pantalla
        _activa = None
        if self.archivo:
            self.archivo.close()
