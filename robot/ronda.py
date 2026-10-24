"""Recorrido de la ronda en serpiente: caminar, parar, posar, fotografiar y analizar (sección 13.3 del plan).

Cada foto se guarda en disco y se analiza en seguida (candidatas → clase →
ubicación). Más adelante el análisis irá en un hilo aparte con una cola, para
que el robot camine mientras tanto.

Estructura de cada ronda:
    datos/rondas/<id_ronda>/
        fotos/c01_p02_izq_alta.png        ← color
        fotos/c01_p02_izq_alta_prof.png   ← profundidad en milímetros (PNG de 16 bits, 0 = sin dato)
        capturas.jsonl                    ← una línea por foto: pose de la cámara, robot, ángulos
        detecciones.jsonl                 ← una línea por rosa vista en una foto (con repetidas)
        rosas.json                        ← las rosas ya juntadas (sin repetidas)
        checkpoint.json                   ← qué paradas ya se hicieron (para continuar si se interrumpe)
        verdad.json, metricas.json        ← solo en simulación
"""

import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

from cuerpo.interfaz import Captura, Cuerpo
from cuerpo.posturas import NEUTRA, posturas
from navegacion.plano import Plano
from navegacion.ruta import Tramo, camino_a_la_base, numero_parada, paradas, serpiente

PROFUNDIDAD_MAX_M = 20.0   # más allá no se guarda (en sim es el cielo; una RGB-D real mide unos pocos metros)


class GuardarCapturas:
    def __init__(self, carpeta: Path):
        self.carpeta = carpeta
        (carpeta / "fotos").mkdir(parents=True, exist_ok=True)
        self.indice = carpeta / "capturas.jsonl"
        self.total = 0
        self.fechas: dict[str, str] = {}   # foto → fecha y hora en que se tomó
        if self.indice.exists():            # se continúa una ronda a medias
            for linea in self.indice.read_text(encoding="utf-8").splitlines():
                fila = json.loads(linea)
                self.fechas[fila["foto"]] = fila["fecha_hora"]
                self.total += 1

    def guardar(self, cap: Captura, camino: int, parada: int, postura: str) -> dict:
        nombre = f"c{camino:02d}_p{parada:02d}_{postura}"
        foto = f"fotos/{nombre}.png"
        Image.fromarray(cap.rgb).save(self.carpeta / foto)
        fila = {
            "foto": foto,
            "profundidad": None,
            "camino": camino,
            "parada": parada,
            "postura": postura,
            "robot_xy": [round(v, 4) for v in cap.robot_xy],
            "cam_pos": [round(float(v), 5) for v in cap.cam_pos],
            "cam_mat": [round(float(v), 6) for v in cap.cam_mat.ravel()],
            "fovy_grados": round(cap.fovy_grados, 4),
            "ancho": cap.ancho,
            "alto": cap.alto,
            **cap.intrinsecos(),
            "angulos": cap.angulos,
            "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if cap.profundidad is not None:
            # 0 = sin dato (cielo o más lejos de lo que mide la cámara)
            prof = np.where(cap.profundidad > PROFUNDIDAD_MAX_M, 0, cap.profundidad)
            mm = np.round(prof * 1000).astype(np.uint16)
            fila["profundidad"] = f"fotos/{nombre}_prof.png"
            Image.fromarray(mm).save(self.carpeta / fila["profundidad"])
        with open(self.indice, "a", encoding="utf-8") as f:
            f.write(json.dumps(fila, ensure_ascii=False) + "\n")
        self.total += 1
        self.fechas[foto] = fila["fecha_hora"]
        return fila


def nueva_carpeta(cfg: dict, base: Path) -> Path:
    id_ronda = f"{cfg['invernadero']['id']}_{datetime.now():%Y-%m-%d_%H%M%S}"
    return base / "rondas" / id_ronda


class Avance:
    """Checkpoint de la ronda (sección 15 del plan): qué paradas ya se hicieron.

    Se guarda después de cada parada en <carpeta>/checkpoint.json, así si se
    acaba la batería o se cae el programa, la ronda sigue donde iba
    (`python main.py --continuar`). También guarda con qué escena se hizo
    (semilla, tipo de rosas, caminos), para seguir con la misma.
    """

    def __init__(self, carpeta: Path, datos: dict):
        self.ruta = carpeta / "checkpoint.json"
        self.datos = datos

    @classmethod
    def nuevo(cls, carpeta: Path, cfg: dict, caminos: list[int]) -> "Avance":
        a = cls(carpeta, {"id_ronda": carpeta.name, "semilla": cfg["sim"]["semilla"], "rosas": cfg["sim"]["rosas"],
                          "caminos": caminos, "hechas": [], "terminada": False,
                          "inicio": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        a.guardar()
        return a

    @classmethod
    def leer(cls, carpeta: Path) -> "Avance":
        return cls(carpeta, json.loads((carpeta / "checkpoint.json").read_text(encoding="utf-8")))

    def guardar(self) -> None:
        temporal = self.ruta.with_suffix(".tmp")
        temporal.write_text(json.dumps(self.datos, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(temporal, self.ruta)

    def hecha(self, camino: int, x: float) -> bool:
        return [camino, round(x, 2)] in self.datos["hechas"]

    def marcar(self, camino: int, x: float) -> None:
        self.datos["hechas"].append([camino, round(x, 2)])
        self.guardar()

    def terminar(self) -> None:
        self.datos["terminada"] = True
        self.guardar()

    @property
    def caminos(self) -> list[int]:
        return self.datos["caminos"]


def ultima_sin_terminar(base: Path) -> Path | None:
    """La ronda más reciente que quedó a medias."""
    for carpeta in sorted((base / "rondas").glob("*"), reverse=True):
        chk = carpeta / "checkpoint.json"
        if chk.exists() and not json.loads(chk.read_text(encoding="utf-8"))["terminada"]:
            return carpeta
    return None


class SeAcaboLaBateria(Exception):
    """Simula batería baja (`--parar-despues`): la ronda se interrumpe y el robot vuelve a la base."""


def _parada(cuerpo: Cuerpo, cfg: dict, plano: Plano, tramo: Tramo, x: float, guardar: GuardarCapturas,
            analizador, avisar) -> None:
    k = numero_parada(plano, cfg, x)
    vistas = 0
    for nombre, angulos in posturas(cfg).items():
        cuerpo.posar(angulos)
        cap = cuerpo.foto()
        fila = guardar.guardar(cap, tramo.camino, k, nombre)
        if analizador is not None:
            nuevas = analizador.analizar(cap, fila["foto"], tramo.camino)
            vistas += len(nuevas)
            with open(guardar.carpeta / "detecciones.jsonl", "a", encoding="utf-8") as f:
                for det in nuevas:
                    f.write(json.dumps(det.a_dict(), ensure_ascii=False) + "\n")
    flecha = "→" if tramo.sentido > 0 else "←"
    avisar(f"  camino {tramo.camino} {flecha}, parada x = {x:4.1f} m: {len(posturas(cfg))} fotos, {vistas} rosas vistas")


def recorrer(cuerpo: Cuerpo, cfg: dict, plano: Plano, guardar: GuardarCapturas, avance: Avance,
             analizador=None, parar_despues: int | None = None, avisar=print) -> bool:
    """Ronda en serpiente desde la base y de vuelta a la base. Salta las paradas ya hechas.

    Devuelve True si terminó todas las paradas; False si se interrumpió (batería).
    """
    base = tuple(cfg["sim"]["base_xy"])
    pendientes = [c for c in avance.caminos
                  if not all(avance.hecha(c, x) for x in paradas(plano, cfg))]
    hechas_ahora = 0
    tramo = None
    try:
        for tramo in serpiente(plano, cfg, pendientes):
            avisar(f"Camino {tramo.camino} {'hacia el fondo' if tramo.sentido > 0 else 'hacia la cabecera'}")
            cuerpo.ir_a(tramo.entrada_x, tramo.y)
            for x in tramo.xs:
                if avance.hecha(tramo.camino, x):
                    continue
                if parar_despues is not None and hechas_ahora >= parar_despues:
                    raise SeAcaboLaBateria
                cuerpo.ir_a(x, tramo.y)
                _parada(cuerpo, cfg, plano, tramo, x, guardar, analizador, avisar)
                avance.marcar(tramo.camino, x)
                hechas_ahora += 1
            cuerpo.posar(NEUTRA)
            cuerpo.ir_a(tramo.salida_x, tramo.y)
    except SeAcaboLaBateria:
        avisar("Batería baja: se guardó el avance y el robot vuelve a la base.")
        cuerpo.posar(NEUTRA)
        cuerpo.ir_a(tramo.salida_x, tramo.y)   # sigue de frente hasta salir del camino (no gira dentro)
        for punto in camino_a_la_base(plano, cuerpo.posicion(), base):
            cuerpo.ir_a(*punto)
        return False
    avisar("Ronda completa: vuelve a la base.")
    for punto in camino_a_la_base(plano, cuerpo.posicion(), base):
        cuerpo.ir_a(*punto)
    avance.terminar()
    return True
