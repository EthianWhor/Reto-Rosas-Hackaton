"""Recorrido de la ronda: caminar, parar, posar, fotografiar y analizar (sección 13.3 del plan).

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
        verdad.json, metricas.json        ← solo en simulación
"""

import json
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

from cuerpo.interfaz import Captura, Cuerpo
from cuerpo.posturas import NEUTRA, posturas
from navegacion.plano import Plano
from navegacion.ruta import SALIDA_M, paradas

PROFUNDIDAD_MAX_M = 20.0   # más allá no se guarda (en sim es el cielo; una RGB-D real mide unos pocos metros)


class GuardarCapturas:
    def __init__(self, carpeta: Path):
        self.carpeta = carpeta
        (carpeta / "fotos").mkdir(parents=True, exist_ok=True)
        self.indice = carpeta / "capturas.jsonl"
        self.total = 0
        self.fechas: dict[str, str] = {}   # foto → fecha y hora en que se tomó

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


def recorrer_camino(cuerpo: Cuerpo, cfg: dict, plano: Plano, camino: int, guardar: GuardarCapturas,
                    analizador=None, avisar=print) -> None:
    poses = posturas(cfg)
    xs = paradas(plano, cfg)
    for k, x in enumerate(xs):
        cuerpo.caminar_hasta(x)
        vistas = 0
        for nombre, angulos in poses.items():
            cuerpo.posar(angulos)
            cap = cuerpo.foto()
            fila = guardar.guardar(cap, camino, k, nombre)
            if analizador is not None:
                nuevas = analizador.analizar(cap, fila["foto"], camino)
                vistas += len(nuevas)
                with open(guardar.carpeta / "detecciones.jsonl", "a", encoding="utf-8") as f:
                    for det in nuevas:
                        f.write(json.dumps(det.a_dict(), ensure_ascii=False) + "\n")
        avisar(f"  camino {camino}, parada {k + 1}/{len(xs)} (x = {x:.1f} m): {len(poses)} fotos, "
               f"{vistas} rosas vistas")
    cuerpo.posar(NEUTRA)
    cuerpo.caminar_hasta(plano.largo_m + SALIDA_M)
