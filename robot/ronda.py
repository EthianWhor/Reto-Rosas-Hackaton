"""Recorrido de la ronda en serpiente: caminar, parar, posar, fotografiar y analizar (sección 13.3 del plan).

Cada foto se guarda en disco y se analiza (candidatas → clase → ubicación) en un hilo
aparte (`AnalisisEnParalelo`): el robot sigue posando o caminando mientras el modelo piensa.
Una parada se marca como hecha en el checkpoint recién cuando se analizaron sus fotos.

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
import math
import os
import queue
import threading
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

from cuerpo.interfaz import Captura, Cuerpo
from cuerpo.posturas import NEUTRA, posturas
from navegacion.plano import Plano
from navegacion.ruta import Tramo, camino_a_la_base, numero_parada, paradas, serpiente
from percepcion.madurez import decidir

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
    """Crea la carpeta de una ronda nueva. Si ya hay una con la misma hora (dos rondas en el
    mismo segundo), le agrega _2, _3... para que nunca compartan checkpoint ni fotos."""
    id_ronda = f"{cfg['invernadero']['id']}_{datetime.now():%Y-%m-%d_%H%M%S}"
    (base / "rondas").mkdir(parents=True, exist_ok=True)
    n = 1
    while True:
        carpeta = base / "rondas" / (id_ronda if n == 1 else f"{id_ronda}_{n}")
        try:
            carpeta.mkdir()
            return carpeta
        except FileExistsError:
            n += 1


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
                          "camas": cfg["sim"]["camas"], "largo_cama_m": cfg["sim"]["largo_cama_m"],
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

    def anotar_obstaculo(self, camino: int, x: float, alto_m: float | None, resultado: str) -> None:
        """resultado: "lo quitaron" (siguió) o "bloqueado" (abandonó el camino)."""
        self.datos.setdefault("obstaculos", []).append(
            {"camino": camino, "x": round(x, 2), "resultado": resultado,
             "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        self.guardar()

    def anotar_senalada(self, punto: tuple[float, float, float], alcanza: bool) -> None:
        self.datos.setdefault("senaladas", []).append([round(float(v), 3) for v in punto])
        if not alcanza:
            self.datos["fuera_de_alcance"] = self.fuera_de_alcance + 1
        self.guardar()

    @property
    def fuera_de_alcance(self) -> int:
        """Óptimas que la cabeza no pudo centrar (muy altas y muy cerca): el puntero quedó cerca."""
        return self.datos.get("fuera_de_alcance", 0)

    @property
    def senaladas(self) -> list[list[float]]:
        """Rosas óptimas que el robot ya señaló (x, y, z), para no señalar dos veces la misma."""
        return self.datos.get("senaladas", [])

    @property
    def obstaculos(self) -> list[dict]:
        return self.datos.get("obstaculos", [])

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


def bateria_baja(cuerpo: Cuerpo, cfg: dict, avance: "Avance") -> bool:
    """Lee la batería (y la guarda en el checkpoint). True si está por debajo de
    `recorrido.bateria_min_pct`: la reserva alcanza para salir del camino y volver a la base."""
    nivel = cuerpo.nivel_bateria()
    if nivel is None:
        return False
    avance.datos["bateria_pct"] = round(nivel, 1)
    return nivel < cfg["recorrido"]["bateria_min_pct"]


class SeAcaboLaBateria(Exception):
    """Simula batería baja (`--parar-despues`): la ronda se interrumpe y el robot vuelve a la base."""


def _senalar_optimas(cuerpo: Cuerpo, cfg: dict, detecciones: list, avance: Avance) -> int:
    """Acción física (sección 1.1 del plan): después de las fotos de una parada, el robot apunta la
    cabeza a cada rosa óptima nueva y la ilumina con el puntero, para que el operario la vea.
    Solo las que salen "óptimo" con las mismas reglas del reporte (seguras); una rosa vista desde
    dos paradas se señala una vez. `accion.tipo: ninguna` lo apaga."""
    acc = cfg.get("accion") or {}
    if acc.get("tipo", "ninguna") != "senalar":
        return 0
    radio = cfg["dedup"]["radio_m"]
    n = 0
    for det in sorted(detecciones, key=lambda d: (d.lado, d.altura_m)):   # un lado y después el otro
        if decidir(det.clase, det.seguro, det.probs, det.diametro_cm, cfg).estado != "optimo":
            continue
        punto = (det.x, det.y, det.altura_m)
        if any(math.dist(punto, p) < radio for p in avance.senaladas):
            continue
        avance.anotar_senalada(punto, cuerpo.senalar(punto, acc["segundos"]))
        n += 1
    return n


class AnalisisEnParalelo:
    """Analiza las fotos en otro hilo, en orden, mientras el robot sigue (sección 8 del plan).

    El robot entrega cada foto con `foto()` y, al terminar una parada, `fin_parada()`. El hilo
    analiza, guarda las rosas en detecciones.jsonl y avisa qué paradas quedaron listas
    (`listas()`). `resultado()` espera el de una parada (para señalar sus óptimas). Con
    `en_paralelo=False` analiza en el momento, como antes (sirve para comparar y para probar).
    Un error del modelo en el hilo se vuelve a lanzar en el hilo del robot.
    """

    def __init__(self, analizador, carpeta: Path, en_paralelo: bool = True):
        self.analizador = analizador
        self.archivo = carpeta / "detecciones.jsonl"
        self.trabajos: queue.Queue = queue.Queue()
        self.terminadas: queue.Queue = queue.Queue()
        self.resultados: dict = {}
        self.listo: dict = {}
        self.de_la_parada: list = []
        self.error = None
        self.hilo = None
        if en_paralelo and analizador is not None:
            self.hilo = threading.Thread(target=self._trabajar, name="analisis", daemon=True)
            self.hilo.start()

    def foto(self, cap: Captura, foto: str, camino: int) -> None:
        self._revisar_error()
        if self.analizador is None:
            return
        if self.hilo is None:
            self._analizar(cap, foto, camino)
        else:
            self.trabajos.put(("foto", cap, foto, camino))

    def fin_parada(self, clave) -> None:
        self.listo[clave] = threading.Event()
        if self.hilo is None:
            self._cerrar_parada(clave)
        else:
            self.trabajos.put(("fin", clave))

    def resultado(self, clave) -> list:
        """Las rosas de una parada (espera a que se analicen)."""
        while not self.listo[clave].wait(0.2):   # revisa seguido: si el modelo falló, no espera para siempre
            self._revisar_error()
        self._revisar_error()
        return self.resultados[clave]

    def listas(self) -> list:
        """Paradas ya analizadas desde la última vez (no espera)."""
        self._revisar_error()
        salida = []
        while not self.terminadas.empty():
            salida.append(self.terminadas.get())
        return salida

    def esperar_todo(self) -> list:
        """Espera a que se analice todo lo entregado y devuelve las paradas que faltaba avisar."""
        if self.hilo is not None:
            self.trabajos.join()
        return self.listas()

    def cerrar(self) -> None:
        if self.hilo is not None:
            self.trabajos.put(None)
            self.hilo.join()
            self.hilo = None

    def _trabajar(self) -> None:
        while True:
            trabajo = self.trabajos.get()
            try:
                if trabajo is None:
                    return
                if self.error is None:               # después de un error no sigue analizando
                    if trabajo[0] == "foto":
                        self._analizar(*trabajo[1:])
                    else:
                        self._cerrar_parada(trabajo[1])
            except Exception as e:                   # se lanza en el hilo del robot
                self.error = e
                for evento in list(self.listo.values()):
                    evento.set()
            finally:
                self.trabajos.task_done()

    def _analizar(self, cap: Captura, foto: str, camino: int) -> None:
        nuevas = self.analizador.analizar(cap, foto, camino)
        self.de_la_parada += nuevas
        with open(self.archivo, "a", encoding="utf-8") as f:
            for det in nuevas:
                f.write(json.dumps(det.a_dict(), ensure_ascii=False) + "\n")

    def _cerrar_parada(self, clave) -> None:
        self.resultados[clave], self.de_la_parada = self.de_la_parada, []
        self.terminadas.put(clave)
        self.listo[clave].set()

    def _revisar_error(self) -> None:
        if self.error is not None:
            raise RuntimeError("falló el análisis de una foto") from self.error


def _parada(cuerpo: Cuerpo, cfg: dict, plano: Plano, tramo: Tramo, x: float, guardar: GuardarCapturas,
            analisis: AnalisisEnParalelo, avance: Avance) -> tuple:
    """Posa, fotografía y entrega las fotos al análisis. Si hay que señalar las óptimas, espera el
    resultado de esta parada (el análisis ya fue corriendo mientras posaba para las otras fotos)."""
    k = numero_parada(plano, cfg, x)
    clave = (tramo.camino, round(x, 2), tramo.sentido)
    for nombre, angulos in posturas(cfg).items():
        cuerpo.posar(angulos)
        cap = cuerpo.foto()
        fila = guardar.guardar(cap, tramo.camino, k, nombre)
        analisis.foto(cap, fila["foto"], tramo.camino)
    analisis.fin_parada(clave)
    if (cfg.get("accion") or {}).get("tipo", "ninguna") != "ninguna" and analisis.analizador is not None:
        avance.datos.setdefault("senaladas_parada", {})[f"{clave[0]}_{clave[1]}"] = _senalar_optimas(
            cuerpo, cfg, analisis.resultado(clave), avance)
    cuerpo.posar(NEUTRA)   # camina derecho: con la cintura girada, un hombro sale del camino
    return clave


def _marcar_listas(claves: list, analisis: AnalisisEnParalelo, avance: Avance, cfg: dict, avisar) -> None:
    """Marca en el checkpoint las paradas ya analizadas y lo avisa (el robot puede ir más adelante)."""
    for camino, x, sentido in claves:
        avance.marcar(camino, x)
        vistas = len(analisis.resultados.get((camino, x, sentido), []))
        senaladas = avance.datos.get("senaladas_parada", {}).pop(f"{camino}_{x}", 0)
        flecha = "→" if sentido > 0 else "←"
        avisar(f"  camino {camino} {flecha}, parada x = {x:4.1f} m: {len(posturas(cfg))} fotos, {vistas} rosas vistas"
               + (f", {senaladas} óptimas señaladas" if senaladas else ""))


class Bloqueado(Exception):
    """El camino tiene un obstáculo que no quitaron."""

    def __init__(self, x_obstaculo: float):
        self.x_obstaculo = x_obstaculo


def _avanzar(cuerpo: Cuerpo, cfg: dict, x_meta: float, y: float, avance: Avance, camino: int, avisar) -> None:
    """Camina por el camino hasta x_meta revisando obstáculos (sección 5.2 y 15 del plan).

    - Obstáculo alto adelante: frena a `distancia_frenado_m` y espera hasta `espera_obstaculo_s`
      (revisa cada 5 s). Si lo quitan, sigue; si no, lanza Bloqueado.
    - Obstáculo bajo (manguera, desnivel) en el tramo: lo cruza a `velocidad_dificil_m_s`.
    """
    rec = cfg["recorrido"]
    frenado = rec["distancia_frenado_m"]
    while True:
        x0, _ = cuerpo.posicion()
        falta = abs(x_meta - x0)
        if falta < 1e-3:
            return
        sentido = 1 if x_meta > x0 else -1
        cuerpo.orientar(0.0 if sentido > 0 else math.pi)
        paso = min(falta, rec["mira_adelante_m"] - frenado)   # avanza de a poco, mirando adelante
        alto, bajo = cuerpo.obstaculos_adelante(paso + frenado)
        lenta = rec["velocidad_dificil_m_s"] if bajo is not None and bajo <= paso + 0.3 else None
        if alto is None or alto - frenado >= paso:
            cuerpo.ir_a(x0 + sentido * paso, y, lenta)
            continue
        if alto - frenado > 0.05:                             # se acerca hasta la distancia de frenado
            cuerpo.ir_a(x0 + sentido * (alto - frenado), y, lenta)
        x_obst = cuerpo.posicion()[0] + sentido * frenado
        avisar(f"  obstáculo en el camino {camino}, metro {x_obst:.1f}: espera a que lo quiten")
        esperado = 0.0
        while esperado < rec["espera_obstaculo_s"]:
            cuerpo.esperar(5.0)
            esperado += 5.0
            alto, _ = cuerpo.obstaculos_adelante(frenado + 0.3)
            if alto is None:
                break
        if alto is not None:
            avance.anotar_obstaculo(camino, x_obst, None, "bloqueado")
            raise Bloqueado(x_obst)
        avance.anotar_obstaculo(camino, x_obst, None, "lo quitaron")
        avisar(f"  lo quitaron después de {esperado:.0f} s: sigue")


def recorrer(cuerpo: Cuerpo, cfg: dict, plano: Plano, guardar: GuardarCapturas, avance: Avance,
             analizador=None, parar_despues: int | None = None, avisar=print) -> bool:
    """Ronda en serpiente desde la base y de vuelta a la base. Salta las paradas ya hechas.

    Si un camino está bloqueado, el robot sale por donde entró (gira dentro del camino: es la única
    vez que lo hace), anota el obstáculo y sigue con los demás caminos desde ese lado.
    Devuelve True si terminó (aunque haya caminos bloqueados); False si se interrumpió (batería).
    """
    analisis = AnalisisEnParalelo(analizador, guardar.carpeta, cfg["percepcion"].get("analisis_en_paralelo", True))
    try:
        return _recorrer(cuerpo, cfg, plano, guardar, avance, analisis, parar_despues, avisar)
    finally:                                   # también si se cierra la ventana: lo ya fotografiado se analiza
        try:
            _marcar_listas(analisis.esperar_todo(), analisis, avance, cfg, avisar)
        finally:
            analisis.cerrar()


def _recorrer(cuerpo: Cuerpo, cfg: dict, plano: Plano, guardar: GuardarCapturas, avance: Avance,
              analisis: AnalisisEnParalelo, parar_despues: int | None, avisar) -> bool:
    base = tuple(cfg["sim"]["base_xy"])
    cola = [c for c in avance.caminos if not all(avance.hecha(c, x) for x in paradas(plano, cfg))]
    desde_cabecera = True
    hechas_ahora = 0
    tramo, dentro = None, False
    try:
        while cola:
            tramo = serpiente(plano, cfg, [cola.pop(0)], desde_cabecera)[0]
            if bateria_baja(cuerpo, cfg, avance):          # ni entra al camino
                raise SeAcaboLaBateria
            nivel = cuerpo.nivel_bateria()
            avisar(f"Camino {tramo.camino} {'hacia el fondo' if tramo.sentido > 0 else 'hacia la cabecera'}"
                   + (f" (batería {nivel:.0f} %)" if nivel is not None else ""))
            cuerpo.ir_a(tramo.entrada_x, tramo.y)
            dentro = True
            try:
                for x in tramo.xs:
                    if avance.hecha(tramo.camino, x):
                        continue
                    if parar_despues is not None and hechas_ahora >= parar_despues:
                        raise SeAcaboLaBateria
                    if bateria_baja(cuerpo, cfg, avance):
                        raise SeAcaboLaBateria
                    _avanzar(cuerpo, cfg, x, tramo.y, avance, tramo.camino, avisar)
                    _parada(cuerpo, cfg, plano, tramo, x, guardar, analisis, avance)
                    hechas_ahora += 1
                    _marcar_listas(analisis.listas(), analisis, avance, cfg, avisar)   # las ya analizadas
                cuerpo.posar(NEUTRA)
                _avanzar(cuerpo, cfg, tramo.salida_x, tramo.y, avance, tramo.camino, avisar)
                desde_cabecera = tramo.salida_x < 0
            except Bloqueado:
                avisar(f"  sigue ahí: abandona el camino {tramo.camino} y sale por donde entró")
                cuerpo.posar(NEUTRA)
                cuerpo.ir_a(tramo.entrada_x, tramo.y)
                desde_cabecera = tramo.entrada_x < 0
            dentro = False
    except SeAcaboLaBateria:
        nivel = cuerpo.nivel_bateria()
        avisar("Batería baja" + (f" ({nivel:.0f} %)" if nivel is not None else "")
               + ": se guardó el avance y el robot vuelve a la base.")
        avance.guardar()
        cuerpo.posar(NEUTRA)
        if dentro:
            try:
                _avanzar(cuerpo, cfg, tramo.salida_x, tramo.y, avance, tramo.camino, avisar)  # sale de frente
            except Bloqueado:
                cuerpo.ir_a(tramo.entrada_x, tramo.y)
        for punto in camino_a_la_base(plano, cuerpo.posicion(), base):
            cuerpo.ir_a(*punto)
        bateria_baja(cuerpo, cfg, avance)                  # anota con cuánto llegó a la base
        _marcar_listas(analisis.esperar_todo(), analisis, avance, cfg, avisar)
        avance.guardar()
        return False
    avisar("Ronda completa: vuelve a la base.")
    for punto in camino_a_la_base(plano, cuerpo.posicion(), base):
        cuerpo.ir_a(*punto)
    bateria_baja(cuerpo, cfg, avance)                      # anota con cuánto llegó a la base
    _marcar_listas(analisis.esperar_todo(), analisis, avance, cfg, avisar)   # lo que faltaba analizar
    avance.terminar()
    return True
