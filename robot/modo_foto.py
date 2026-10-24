"""Modo foto: la demo en vivo (sección 7.5 del plan).

El jurado trae una rosa (o una foto) y el robot la analiza con **el mismo
pipeline de la ronda**: el detector del equipo encuentra las rosas, RosaNet dice
su estado y las reglas del robot deciden (óptimo, inmaduro, pasado o dudosa).
Muestra la foto con las cajas pintadas por estado, la confianza y los consejos
de la finca para aprender a reconocerla.

Se corre desde la carpeta robot/:
    python modo_foto.py foto.jpg              -> analiza una foto (o varias, acepta comodines)
    python modo_foto.py --webcam              -> cámara en vivo: ESPACIO analiza, Q sale
    python modo_foto.py foto.jpg --reporte    -> además arma un mini reporte (Excel + JSON) como una ronda
    python modo_foto.py foto.jpg --enviar     -> y lo manda a la app con el envío del config (envio.metodo)
    python modo_foto.py --webcam --enviar --config config/demo.yaml   -> a la app (Supabase), con las fotos de las dudosas
    python modo_foto.py --webcam --auto --enviar --config config/demo.yaml   -> sin teclas: cuando reconoce una rosa
        en el cuadro, la manda sola a la app (otra vez cuando se saca la rosa y se pone otra)

Límites (decirlos en la demo):
- Sin cámara de profundidad no se sabe el tamaño de la cabeza, así que aquí no
  se predice "lista mañana" (en la ronda sí).
- El detector del equipo está hecho para escenas del invernadero (rosas lejanas)
  y no sirve para una rosa en la mano: descarta cajas grandes y, si se le quita
  ese límite, marca caras, manos y objetos rojos. Por eso, si no encuentra rosas,
  con la cámara se analiza solo lo que está dentro del CUADRO GUÍA del centro
  (con una foto, la foto completa). Si la cámara no muestra imagen o el cuadro no
  tiene nada rojizo, dice que no ve una rosa. Un objeto rojo dentro del cuadro se
  analiza como si fuera una rosa: es un límite de la demo (en el invernadero el
  robot usa el detector, no el cuadro).
- El modelo todavía se está mejorando: cuando el equipo suba uno nuevo a
  modelos/, este modo lo usa solo.
"""

import argparse
import glob
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import configuracion
from cuerpo.interfaz import Captura
from percepcion import modelo_equipo
from percepcion.candidatas import Candidata
from percepcion.madurez import decidir

# Mismos colores que el reporte Excel y el juego de la tablet
COLORES = {"optimo": (192, 57, 43), "lista_manana": (230, 126, 34), "inmaduro": (91, 127, 58),
           "pasado": (142, 90, 43), "dudosa": (128, 128, 128)}
NOMBRES = {"optimo": "Óptimo: cortar hoy", "lista_manana": "Lista mañana", "inmaduro": "Inmaduro: no cortar",
           "pasado": "Pasado", "dudosa": "Dudosa: revisar"}


@dataclass
class RosaFoto:
    caja: list[int]
    estado: str              # optimo | inmaduro | pasado | dudosa (sin profundidad no hay lista_manana)
    clase_red: str           # lo que dijo RosaNet
    confianza: float
    probs: dict
    tips: dict = field(default_factory=dict)
    foto_completa: bool = False   # True si se tomó la foto entera como una sola rosa


DESVIO_MIN_IMAGEN = 15    # menos variación que esto = imagen en blanco (cámara tapada o bloqueada)
ROJO_MIN = 0.03           # con la cámara: fracción mínima de píxeles rojizos en el cuadro para analizarlo
GUIA_FRAC = 0.6           # lado del cuadro guía de la cámara, como fracción del lado corto de la imagen
AUTO_CADA_S = 1.0         # --auto: cada cuánto mira si hay una rosa (el análisis tarda ~0,5 s sin GPU)
AUTO_IGUALES = 2          # --auto: lecturas seguidas con el mismo resultado antes de mandar (la rosa quieta)
# --auto: tamaño mínimo (fracción del cuadro) de la mancha de rojo vivo más grande para mirar si hay una rosa.
# Medido con la webcam en un salón: el rojo general acepta piel y pelo (una cara dio 27 % y se mandó como
# "inmaduro"), y hasta el rojo saturado aparece en hebras de pelo castaño (1,2 %). En una rosa el rojo es UNA
# mancha compacta: pelo y caras dieron como mucho 0,26 %, las rosas (de verdad o en un celular) 1,8–18 %.
# Un botón muy oscuro tiene que llenar el cuadro. Con ESPACIO basta ROJO_MIN, porque ahí decide la persona.
AUTO_MANCHA_MIN = 0.008


def fraccion_roja(rgb: np.ndarray) -> float:
    """Fracción de píxeles de pétalo rojo (o rosado/magenta, como en una pantalla de celular)."""
    import cv2
    if rgb.size == 0:
        return 0.0
    hsv = cv2.cvtColor(np.ascontiguousarray(rgb), cv2.COLOR_RGB2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    return float((((h <= 12) | (h >= 150)) & (s >= 40) & (v >= 20)).mean())   # incluye el rojo oscuro de un botón


def mancha_roja(rgb: np.ndarray) -> float:
    """Tamaño (fracción de la imagen) de la mancha más grande de rojo vivo, como un pétalo o un botón.
    Se abre la máscara (5 × 5 px) para borrar hebras de pelo y bordes sueltos."""
    import cv2
    if rgb.size == 0:
        return 0.0
    hsv = cv2.cvtColor(np.ascontiguousarray(rgb), cv2.COLOR_RGB2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    mascara = ((((h <= 12) | (h >= 160)) & (s >= 120) & (v >= 15)) * 255).astype(np.uint8)   # v bajo: botón oscuro
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, _, stats, _ = cv2.connectedComponentsWithStats(mascara)
    return float(stats[1:, cv2.CC_STAT_AREA].max()) / mascara.size if n > 1 else 0.0


def cuadro_guia(ancho: int, alto: int) -> tuple[int, int, int, int]:
    lado = int(GUIA_FRAC * min(ancho, alto))
    x1, y1 = (ancho - lado) // 2, (alto - lado) // 2
    return x1, y1, x1 + lado, y1 + lado


class Analizador:
    """Las mismas piezas que usa la ronda, armadas como en el robot real (sin oráculo)."""

    def __init__(self, cfg: dict):
        from percepcion.analisis import crear_analizador
        real = dict(cfg, modo="real")             # foto de verdad: nada de oráculo
        eleccion = modelo_equipo.elegir(real)
        piezas = crear_analizador(real, eleccion, plano=None)
        self.candidatas, self.clasificador = piezas.candidatas, piezas.clasificador
        self.eleccion = eleccion
        self.cfg = cfg
        self.tamano_min = cfg["percepcion"]["tamano_min_px"]

    def analizar(self, rgb: np.ndarray, guia: tuple[int, int, int, int] | None = None) -> list[RosaFoto]:
        """Rosas de la foto. Si el detector no encuentra ninguna (una rosa de cerca), se analiza solo
        la zona `guia` (el cuadro de la cámara) o, sin guía, la foto completa, pero solo si ahí parece
        haber una rosa. `self.motivo` dice por qué no hubo rosas."""
        alto, ancho = rgb.shape[:2]
        self.motivo = ""
        if rgb.std() < DESVIO_MIN_IMAGEN:
            self.motivo = "La cámara no muestra imagen (¿está tapada o la usa otro programa?)."
            return []
        cap = Captura(rgb, None, np.zeros(3), np.eye(3), 43.0, (0.0, 0.0))
        cands = [c for c in self.candidatas.buscar(cap)
                 if min(c.bbox[2] - c.bbox[0], c.bbox[3] - c.bbox[1]) >= self.tamano_min]
        foto_completa = not cands
        if foto_completa:                         # una rosa de cerca: la zona guía (o la foto) es la rosa
            zona = guia or (0, 0, ancho, alto)
            x1, y1, x2, y2 = zona
            # con la cámara, no analizar un cuadro vacío; con una foto dada a propósito, no se filtra
            if guia is not None and fraccion_roja(rgb[y1:y2, x1:x2]) < ROJO_MIN:
                self.motivo = "No veo una rosa dentro del cuadro. Acércala y ponla dentro del cuadro blanco."
                return []
            cands = [Candidata(zona)]
        salida = []
        for cand, res in zip(cands, self.clasificador.clasificar(cap, cands)):
            # sin profundidad no hay diámetro: el tamaño no suma y no puede salir "lista mañana"
            m = decidir(res["clase"], res["seguro"], res["probs"], 0.0, self.cfg)
            estado = "inmaduro" if m.estado == "lista_manana" else m.estado
            salida.append(RosaFoto([int(v) for v in cand.bbox], estado, res["clase"], res["confianza"],
                                   res["probs"], res.get("tips", {}), foto_completa))
        return salida


ANCHO_MIN_DIBUJO = 900   # una foto de una sola rosa suele ser pequeña: se agranda para que se lea en la demo


def _fuente(tamano: int):
    """Arial (trae tildes: "Óptimo"); si no está, la de Pillow."""
    for nombre in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(nombre, tamano)
        except OSError:
            pass
    return ImageFont.load_default(size=tamano)


def _se_tapan(a, b) -> bool:
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def dibujar(rgb: np.ndarray, rosas: list[RosaFoto]) -> Image.Image:
    """La foto con una caja y una etiqueta por rosa, en el color de su estado, y el conteo abajo."""
    img = Image.fromarray(rgb).convert("RGB")
    escala = max(1.0, ANCHO_MIN_DIBUJO / img.width)
    if escala > 1:
        img = img.resize((round(img.width * escala), round(img.height * escala)), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    grosor = max(3, img.width // 250)
    fuente = _fuente(max(18, img.width // 60))
    cajas = [tuple(round(v * escala) for v in r.caja) for r in rosas]
    puestas = []                                  # etiquetas ya dibujadas, para no taparlas
    for i, r in enumerate(rosas, start=1):
        color = COLORES[r.estado]
        x1, y1, x2, y2 = cajas[i - 1]
        otras = puestas + [c for k, c in enumerate(cajas) if k != i - 1]
        d.rectangle([x1, y1, x2, y2], outline=color, width=grosor)
        texto = f"{i}. {NOMBRES[r.estado]} {r.confianza:.0%}"   # el número es el de "Rosa N" en la consola
        caja_txt = d.textbbox((0, 0), texto, font=fuente)
        ancho_txt, alto_txt = caja_txt[2] + 10, caja_txt[3] + 8
        tx = max(0, min(x1, img.width - ancho_txt))          # que la etiqueta no se salga de la foto
        # arriba de la caja, abajo, o adentro arriba: la primera que no tape otra etiqueta ni otra rosa
        opciones = [y1 - alto_txt, y2 + grosor, y1 + grosor]
        ty = next((y for y in opciones if 0 <= y <= img.height - alto_txt
                   and not any(_se_tapan((tx, y, tx + ancho_txt, y + alto_txt), p) for p in otras)),
                  next((y for y in opciones if 0 <= y <= img.height - alto_txt), 0))
        puestas.append((tx, ty, tx + ancho_txt, ty + alto_txt))
        d.rectangle(puestas[-1], fill=color)
        d.text((tx + 5, ty + 3), texto, fill="white", font=fuente)
    conteo = resumen(rosas)
    pie = "   ".join(f"{NOMBRES[e].split(':')[0]}: {n}" for e, n in conteo.items() if n)
    if pie:
        caja_txt = d.textbbox((0, 0), pie, font=fuente)
        d.rectangle([0, img.height - (caja_txt[3] + 16), img.width, img.height], fill=(0, 0, 0))
        d.text((10, img.height - caja_txt[3] - 10), pie, fill="white", font=fuente)
    return img


def resumen(rosas: list[RosaFoto]) -> dict:
    return {e: sum(r.estado == e for r in rosas) for e in ("optimo", "inmaduro", "pasado", "dudosa")}


def explicar(rosas: list[RosaFoto], motivo: str = "") -> str:
    """Texto para leer en la demo: qué es cada rosa y qué mirar (tips de la finca, ml/stages.py)."""
    if not rosas:
        return motivo or "No encontré rosas en la foto."
    lineas = []
    if rosas[0].foto_completa:
        lineas.append("(No encontré rosas en una escena: analicé la rosa de cerca, como UNA rosa.)")
    for i, r in enumerate(rosas, start=1):
        probs = ", ".join(f"{k} {v:.0%}" for k, v in sorted(r.probs.items(), key=lambda kv: -kv[1]))
        lineas.append(f"Rosa {i}: {NOMBRES[r.estado]} (la red dice {r.clase_red} con {r.confianza:.0%}; {probs})")
        if r.estado == "dudosa":
            lineas.append("   La red no está segura: que la revise alguien con experiencia o tomar otra foto más cerca.")
        for t in r.tips.get("mirar", []):
            lineas.append(f"   - {t}")
        if r.tips.get("diferencia"):
            lineas.append(f"   > {r.tips['diferencia']}")
    return "\n".join(lineas)


def id_ronda_demo(cfg: dict, ahora: datetime) -> str:
    return f"{cfg['invernadero']['id']}_DEMO_{ahora:%Y-%m-%d_%H%M%S}"


def mini_reporte(rosas: list[RosaFoto], cfg: dict, nombre_foto: str, ahora: datetime | None = None):
    """Reporte con el mismo formato de la ronda (sección 10), con un solo "cuadrante" DEMO, para la app.

    `foto` es `fotos/<nombre>` dentro de datos/rondas/<id_ronda>/, como en la ronda (ver `guardar_como_ronda`).
    """
    from reporte.tabla import COLUMNAS_LISTAS, Reporte, prioridad
    ahora = ahora or datetime.now()
    inv = cfg["invernadero"]["id"]
    nombre_foto = f"fotos/{nombre_foto}"
    c = resumen(rosas)
    cuadrante = {"cuadrante_id": f"{inv}-DEMO", "cama": 0, "tramo": 0, "desde_m": 0, "hasta_m": 0,
                 "optimo": c["optimo"], "lista_manana": 0, "inmaduro": c["inmaduro"], "pasado": c["pasado"],
                 "dudosa": c["dudosa"], "total": len(rosas),
                 "prioridad": prioridad(c["optimo"], 0, cfg["reporte"]["optimo_prioridad_alta"]), "orden": 1}
    fecha_hora = f"{ahora:%Y-%m-%d %H:%M:%S}"
    listas = [{k: v for k, v in {
        "rosa_id": f"{inv}-DEMO-{i}", "estado": "optimo", "cuadrante_id": cuadrante["cuadrante_id"], "cama": 0,
        "lado": "", "metro_en_cama": 0, "altura_m": 0, "diametro_cm": None, "confianza": r.confianza,
        "foto": nombre_foto, "fecha_hora": fecha_hora}.items() if k in COLUMNAS_LISTAS}
        for i, r in enumerate(rosas, start=1) if r.estado == "optimo"]
    dudosas = [{"rosa_id": f"{inv}-DEMO-{i}", "clase_modelo": r.clase_red, "confianza": r.confianza,
                "cuadrante_id": cuadrante["cuadrante_id"], "cama": 0, "lado": "", "metro_en_cama": 0,
                "altura_m": 0, "foto": nombre_foto, "fecha_hora": fecha_hora}
               for i, r in enumerate(rosas, start=1) if r.estado == "dudosa"]
    id_ronda = id_ronda_demo(cfg, ahora)
    return Reporte(id_ronda=id_ronda, invernadero=inv, fecha=f"{ahora:%Y-%m-%d}", inicio=fecha_hora, fin=fecha_hora,
                   cuadrantes=[cuadrante], rosas_listas=listas, todas=[], dudosas=dudosas,
                   ronda=[("id_ronda", id_ronda), ("modo", "foto (demo en vivo)"), ("foto", nombre_foto),
                          ("rosas en la foto", len(rosas))])


def guardar_como_ronda(rgb: np.ndarray, nombre: str, rosas: list[RosaFoto], carpeta_ronda: Path, inv: str) -> None:
    """La foto y las cajas en datos/rondas/<id_ronda>/, como una ronda: así el envío a Supabase
    encuentra el recorte de cada dudosa (reporte/fotos.py) igual que en la ronda. Sin checkpoint,
    `main.py --continuar` no la toma por una ronda a medias."""
    (carpeta_ronda / "fotos").mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgb).save(carpeta_ronda / "fotos" / nombre)
    lineas = [json.dumps({"rosa_id": f"{inv}-DEMO-{i}", "foto": f"fotos/{nombre}", "bbox": r.caja})
              for i, r in enumerate(rosas, start=1)]
    (carpeta_ronda / "detecciones.jsonl").write_text("".join(l + "\n" for l in lineas), encoding="utf-8")


def procesar(rgb: np.ndarray, nombre: str, analizador: Analizador, carpeta: Path, cfg: dict,
             reporte: bool = False, enviar: bool = False, guia=None, rosas: list[RosaFoto] | None = None
             ) -> list[RosaFoto]:
    """Analiza (o usa `rosas`, si ya se analizó esa misma imagen), guarda la foto anotada y, si se pide,
    arma el mini reporte y lo envía."""
    if rosas is None:
        rosas = analizador.analizar(rgb, guia)
    carpeta.mkdir(parents=True, exist_ok=True)
    anotada = carpeta / f"{Path(nombre).stem}_anotada.jpg"
    dibujar(rgb, rosas).save(anotada, quality=92)
    (carpeta / f"{Path(nombre).stem}.json").write_text(
        json.dumps({"foto": nombre, "rosas": [asdict(r) for r in rosas], "conteo": resumen(rosas)},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n=== {nombre} ===")
    print(explicar(rosas, analizador.motivo))
    print(f"Foto anotada: {anotada}")
    if reporte or enviar:
        from reporte import archivos
        datos = configuracion.ruta(cfg["datos_dir"])
        ahora = datetime.now()
        guardar_como_ronda(rgb, nombre, rosas, datos / "rondas" / id_ronda_demo(cfg, ahora), cfg["invernadero"]["id"])
        mini = mini_reporte(rosas, cfg, nombre, ahora)
        rutas = archivos.guardar(mini, datos / "salida", cfg["reporte"]["formatos"], avisar=print,
                                 ya_enviados=datos / "enviados", base=f"reporte_{mini.id_ronda}")
        print("Mini reporte: " + ", ".join(str(r) for r in rutas))
        if enviar:
            from reporte import envio
            bandeja, enviador, conexion = envio.crear(cfg)
            print(f"Envío: {envio.describir(bandeja.intentar(enviador, conexion))}")
    return rosas


class Disparo:
    """--auto: decide cuándo analizar y mandar sin tocar el teclado. Manda cuando la misma lectura sale
    `AUTO_IGUALES` veces seguidas, y no vuelve a mandar hasta que el cuadro quede vacío (sacar la rosa)
    también `AUTO_IGUALES` veces seguidas: una lectura vacía suelta (una mano que tapa la rosa un
    momento) no cuenta como sacarla. `rosas` es la lectura que se manda, para no analizar dos veces."""

    def __init__(self):
        self.ultima, self.iguales, self.enviada, self.vacias, self.rosas = None, 0, False, 0, []

    def ver(self, rosas: list[RosaFoto]) -> bool:
        """Una lectura del cuadro; True = es hora de mandarla (está en `self.rosas`)."""
        if not rosas:
            self.vacias += 1
            if self.vacias >= AUTO_IGUALES:   # cuadro vacío de verdad: listo para otra rosa
                self.ultima, self.iguales, self.enviada = None, 0, False
            return False
        self.vacias = 0
        lectura = tuple(r.estado for r in rosas)
        self.iguales = self.iguales + 1 if lectura == self.ultima else 1
        self.ultima = lectura
        if self.enviada or self.iguales < AUTO_IGUALES:
            return False
        self.enviada, self.rosas = True, rosas
        return True

    def aviso(self) -> str:
        if self.enviada:
            return "Enviada a la app. Saca la rosa para mandar otra"
        if self.ultima:
            return f"Reconociendo: {NOMBRES[self.ultima[0]]}..."
        return "AUTO: esperando una rosa"


def webcam(analizador: Analizador, carpeta: Path, cfg: dict, reporte: bool, enviar: bool, indice: int = 0,
           auto: bool = False) -> int:
    """Cámara en vivo (la webcam `indice`).
    Con `auto`, analiza sola cada `AUTO_CADA_S` y procesa (y manda) cada rosa nueva que reconoce."""
    import time
    import cv2
    cam = cv2.VideoCapture(indice)
    if not cam.isOpened():
        print(f"No se pudo abrir la cámara {indice}.")
        return 1
    print("Cámara en vivo: ESPACIO analiza la imagen, Q sale."
          + (" AUTO: cuando reconoce una rosa en el cuadro, la " + ("manda a la app." if enviar else "analiza.")
             if auto else ""))
    resultado = None
    disparo, proxima = Disparo(), 0.0
    try:
        while True:
            ok, cuadro = cam.read()
            if not ok:
                print("La cámara no entregó imagen.")
                return 1
            vista = cuadro.copy()
            alto, ancho = vista.shape[:2]
            gx1, gy1, gx2, gy2 = cuadro_guia(ancho, alto)
            cv2.rectangle(vista, (gx1, gy1), (gx2, gy2), (255, 255, 255), 2)
            cv2.putText(vista, "Pon la rosa dentro del cuadro", (gx1, max(25, gy1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(vista, "ESPACIO: analizar   Q: salir", (15, alto - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (255, 255, 255), 2)
            if auto:
                cv2.putText(vista, disparo.aviso(), (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            cv2.imshow("Robot rosas - camara", vista)
            tecla = cv2.waitKey(1) & 0xFF
            if tecla in (ord("q"), 27):
                return 0
            disparar, leidas = tecla == ord(" "), None
            if auto and not disparar and time.monotonic() >= proxima:
                proxima = time.monotonic() + AUTO_CADA_S
                rgb = cv2.cvtColor(cuadro, cv2.COLOR_BGR2RGB)
                gx1, gy1, gx2, gy2 = cuadro_guia(rgb.shape[1], rgb.shape[0])
                # lectura rápida: si el cuadro no tiene nada rojo ni se analiza (no gasta la red)
                hay_rojo = mancha_roja(rgb[gy1:gy2, gx1:gx2]) >= AUTO_MANCHA_MIN
                disparar = disparo.ver(analizador.analizar(rgb, (gx1, gy1, gx2, gy2)) if hay_rojo else [])
                if disparar:
                    leidas = disparo.rosas   # la misma imagen que se acaba de leer: no se analiza dos veces
                    print("\nAUTO: rosa reconocida, " + ("la mando a la app..." if enviar else "la analizo."))
            if disparar:
                rgb = cv2.cvtColor(cuadro, cv2.COLOR_BGR2RGB)   # OpenCV entrega BGR; la red espera RGB
                nombre = f"webcam_{datetime.now():%H%M%S}.jpg"
                carpeta.mkdir(parents=True, exist_ok=True)
                Image.fromarray(rgb).save(carpeta / nombre)   # la foto original, para revisarla después
                guia = cuadro_guia(rgb.shape[1], rgb.shape[0])
                rosas = procesar(rgb, nombre, analizador, carpeta, cfg, reporte, enviar, guia, leidas)
                resultado = cv2.cvtColor(np.asarray(dibujar(rgb, rosas)), cv2.COLOR_RGB2BGR)
                cv2.imshow("Robot rosas - resultado", resultado)
    finally:
        cam.release()
        cv2.destroyAllWindows()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("fotos", nargs="*", help="Fotos a analizar (acepta comodines)")
    p.add_argument("--webcam", nargs="?", const=0, type=int, metavar="N", help="Usar la cámara N (por defecto 0)")
    p.add_argument("--reporte", action="store_true", help="Armar un mini reporte (Excel + JSON) como el de la ronda")
    p.add_argument("--enviar", action="store_true", help="Enviar el mini reporte con envio.metodo del config")
    p.add_argument("--auto", action="store_true",
                   help="Con la cámara: analizar y mandar solo, sin ESPACIO, cada vez que reconoce una rosa nueva")
    p.add_argument("--salida", type=Path, help="Carpeta para las fotos anotadas (por defecto datos/modo_foto/<hora>)")
    p.add_argument("--config", type=Path, help="Otro archivo de configuración (p. ej. config/demo.yaml, para enviar a la app)")
    args = p.parse_args(argv)
    if not args.fotos and args.webcam is None:
        p.print_help()
        return 2

    cfg = configuracion.cargar(args.config)
    try:
        analizador = Analizador(cfg)
    except (RuntimeError, ValueError) as e:
        print(f"ERROR: el modelo del equipo no está listo: {e}")
        return 1
    print(f"Modelo: candidatas = {analizador.eleccion['candidatas']}, clasificador = {analizador.eleccion['clasificador']}")
    carpeta = args.salida or configuracion.ruta(cfg["datos_dir"]) / "modo_foto" / f"{datetime.now():%Y-%m-%d_%H%M%S}"

    if args.webcam is not None:
        return webcam(analizador, carpeta, cfg, args.reporte, args.enviar, args.webcam, args.auto)
    rutas = [Path(f) for patron in args.fotos for f in (glob.glob(patron) or [patron])]
    for ruta in rutas:
        if not ruta.exists():
            print(f"No existe: {ruta}")
            continue
        with Image.open(ruta) as im:
            rgb = np.asarray(im.convert("RGB"))
        procesar(rgb, ruta.name, analizador, carpeta, cfg, args.reporte, args.enviar)
    return 0


if __name__ == "__main__":
    sys.exit(main())
