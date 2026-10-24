"""Arranca la ronda del robot (ver PLAN_robot_rosas_X2.md).

Revisa qué ofrece el modelo del equipo en ml/, arma el invernadero de prueba
(2 camas de 10 m) y sale de la base a recorrer todos sus caminos en serpiente
(ida por uno, vuelta por el siguiente) y vuelve a la base. Para cada 1,25 m,
toma las 4 posturas, guarda las fotos (color + profundidad) en datos/rondas/,
encuentra y ubica cada rosa (cama, metro, altura), junta las repetidas,
compara el resultado con la verdad de la simulación, arma el reporte Excel +
JSON y lo envía al dashboard cuando "aparece" el WiFi al volver a la base.

Se corre desde la carpeta robot/:
    python main.py                     -> ronda por todos los caminos, reporte y envío
    python main.py --ventana           -> lo mismo, mirando el visor de MuJoCo
    python main.py --camino 1          -> solo un camino (0 = la orilla, solo ve la cama 1)
    python main.py --revisar           -> solo revisa todo, carga la escena y toma una foto de prueba
    python main.py --rosas cartel      -> con fotos reales de rosas: piensa con el modelo del equipo
    python main.py --parar-despues 5   -> simula batería baja: para tras 5 paradas y vuelve a la base
    python main.py --continuar         -> sigue la última ronda que quedó a medias
"""

import argparse
import json
import math
import sys
import time
from datetime import datetime
from pathlib import Path

import configuracion
from percepcion import modelo_equipo


def leer_argumentos(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config", type=Path, help="Otro archivo de configuración")
    p.add_argument("--modo", choices=sorted(configuracion.OPCIONES["modo"]))
    p.add_argument("--candidatas", choices=sorted(configuracion.OPCIONES["percepcion.candidatas"]))
    p.add_argument("--clasificador", choices=sorted(configuracion.OPCIONES["percepcion.clasificador"]))
    p.add_argument("--rosas", choices=sorted(configuracion.OPCIONES["sim.rosas"]))
    p.add_argument("--camino", type=int, help="Recorrer solo este camino (por defecto, los de sim.caminos)")
    p.add_argument("--semilla", type=int, help="Semilla de la escena (misma semilla = mismas rosas)")
    p.add_argument("--revisar", action="store_true", help="Solo revisar y tomar una foto de prueba, sin caminar")
    p.add_argument("--ventana", action="store_true", help="Abrir el visor de MuJoCo")
    p.add_argument("--continuar", nargs="?", const="ultima", metavar="ID_RONDA",
                   help="Seguir una ronda que quedó a medias (sin ID: la última)")
    p.add_argument("--parar-despues", type=int, metavar="N",
                   help="Simular batería baja: interrumpir después de N paradas y volver a la base")
    return p.parse_args(argv)


def mostrar_percepcion(cfg: dict) -> dict:
    estado = modelo_equipo.revisar(cfg)
    print("Modelo del equipo (ml/):")
    for comp, e in estado.items():
        print(f"  {comp:<12} {'listo' if e['listo'] else 'no listo'}: {e['motivo']}")
    eleccion = modelo_equipo.elegir(cfg, estado)
    print(f"Percepción: candidatas = {eleccion['candidatas']}, clasificador = {eleccion['clasificador']}")
    for nota in eleccion["notas"]:
        print(f"  nota: {nota}")
    return eleccion


def guardar_json(ruta: Path, datos) -> None:
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)


def cuadrantes_bloqueados(obstaculos: list[dict], plano, cfg: dict) -> list[str]:
    """Cuadrantes junto a un camino bloqueado: los de las camas a los dos lados, en el tramo del
    obstáculo. Quedaron revisados solo en parte (desde el otro camino de la cama, si lo hay).
    Es lo que la app recibe en "obstaculos"."""
    from navegacion.plano import tramo
    from percepcion.dedup import cuadrante_id
    salida = []
    for o in obstaculos:
        if o["resultado"] != "bloqueado":
            continue
        c = plano.camino(o["camino"])
        t = min(tramo(min(max(o["x"], 0.0), plano.largo_m - 1e-6), plano.tramo_m),
                math.ceil(plano.largo_m / plano.tramo_m))
        for cama in (c.cama_der, c.cama_izq):
            if cama is not None:
                cid = cuadrante_id(cfg["invernadero"]["id"], cama, t)
                if cid not in salida:
                    salida.append(cid)
    return salida


def mostrar_resumen(rosas, resultado: dict, analizador) -> None:
    print(f"Rosas: {len(analizador.detecciones)} vistas en las fotos → {len(rosas)} sin repetir")
    print("Métricas contra la verdad:")
    for clave, valor in resultado.items():
        print(f"  {clave}: {valor}")
    print(f"  descartadas: {analizador.descartadas}")


def correr_sim(cfg: dict, eleccion: dict, args: argparse.Namespace, reanudar=None) -> int:
    from PIL import Image

    import metricas
    import ronda
    from cuerpo.sim_backend import CuerpoSim
    from navegacion.plano import armar_plano
    from percepcion.analisis import Deteccion, crear_analizador
    from percepcion.dedup import juntar
    from reporte import archivos, envio
    from reporte.tabla import armar_reporte
    from sim.escena_invernadero import CAMARA, armar_escena, resolucion

    plano = armar_plano(cfg)
    base = configuracion.ruta(cfg["datos_dir"])
    if reanudar is not None:
        carpeta, avance = reanudar
        caminos = avance.caminos
    else:
        caminos = [args.camino] if args.camino is not None else (
            cfg["sim"]["caminos"] or [c.numero for c in plano.caminos])
    escena = armar_escena(cfg, en_base=not args.revisar)
    m = escena.m
    ancho, alto = resolucion(cfg)
    print(f"Invernadero de prueba: {len(plano.camas)} camas de {plano.largo_m:g} m, {len(escena.verdad)} rosas")
    print(f"Ruta en serpiente por los caminos {caminos}, desde la base y de vuelta")
    print(f"Cámara de la cabeza: {ancho} x {alto}, fovy {m.camera(CAMARA).fovy[0]:.1f}°, "
          f"giro de las fotos {math.degrees(cfg['recorrido']['giro_diagonal_rad']):.0f}°")

    if args.revisar:
        cuerpo = CuerpoSim(escena, cfg)
        try:
            cuerpo.pararse()
            salida = base / "fotos" / "prueba_camara.png"
            salida.parent.mkdir(parents=True, exist_ok=True)
            cap = cuerpo.foto()
            Image.fromarray(cap.rgb).save(salida)
            print(f"Cámara a {cap.cam_pos[2]:.2f} m del piso. Foto de prueba: {salida}")
        finally:
            cuerpo.cerrar()
        if args.ventana:
            import mujoco.viewer
            mujoco.viewer.launch(escena.m, escena.d)
        return 0

    analizador = crear_analizador(cfg, eleccion, escena.plano, escena.verdad)
    if reanudar is not None:
        # lo que ya se vio antes de la interrupción
        archivo = carpeta / "detecciones.jsonl"
        if archivo.exists():
            analizador.detecciones = [Deteccion(**json.loads(l))
                                      for l in archivo.read_text(encoding="utf-8").splitlines()]
        print(f"Continúa la ronda {carpeta.name}: {len(avance.datos['hechas'])} paradas ya hechas")
    else:
        carpeta = ronda.nueva_carpeta(cfg, base)
        avance = ronda.Avance.nuevo(carpeta, cfg, caminos)
        guardar_json(carpeta / "verdad.json",
                     {"semilla": cfg["sim"]["semilla"], "rosas": [r.a_dict() for r in escena.verdad]})
    guardar = ronda.GuardarCapturas(carpeta)
    camas = {c for n in caminos for c in (plano.camino(n).cama_izq, plano.camino(n).cama_der) if c is not None}

    visor = None
    if args.ventana:
        import mujoco.viewer
        visor = mujoco.viewer.launch_passive(escena.m, escena.d)
    cuerpo = CuerpoSim(escena, cfg, visor)
    inicio = time.time()
    try:
        cuerpo.pararse()
        completa = ronda.recorrer(cuerpo, cfg, plano, guardar, avance, analizador, args.parar_despues)
    except KeyboardInterrupt:
        print(f"Ronda interrumpida. El avance quedó guardado: python main.py --continuar {carpeta.name}")
        return 1
    finally:
        cuerpo.cerrar()
        if visor is not None:
            visor.close()
    print(f"{guardar.total} fotos en {carpeta} ({time.time() - inicio:.0f} s)")
    if not completa:
        print(f"Para seguir donde quedó: python main.py --continuar {carpeta.name}")
        return 0
    hora_inicio = datetime.strptime(avance.datos["inicio"], "%Y-%m-%d %H:%M:%S")

    rosas = juntar(analizador.detecciones, cfg["dedup"]["radio_m"], cfg["invernadero"]["id"])
    guardar_json(carpeta / "rosas.json", [r.a_dict() for r in rosas])
    hora_fin = datetime.now()
    rep = armar_reporte(rosas, escena.plano, camas, cfg, {
        "id_ronda": carpeta.name,
        "inicio": f"{hora_inicio:%Y-%m-%d %H:%M:%S}",
        "fin": f"{hora_fin:%Y-%m-%d %H:%M:%S}",
        "fechas_fotos": guardar.fechas,
        "obstaculos": cuadrantes_bloqueados(avance.obstaculos, plano, cfg),
        "ronda": [
            ("id_ronda", carpeta.name),
            ("modo", cfg["modo"]),
            ("inicio / fin", f"{hora_inicio:%Y-%m-%d %H:%M:%S} / {hora_fin:%Y-%m-%d %H:%M:%S}"),
            ("caminos recorridos", f"{len(caminos)} de {len(escena.plano.caminos)}, en serpiente: {caminos}"),
            ("paradas cada (m)", cfg["recorrido"]["paso_entre_paradas_m"]),
            ("giro de las fotos (°)", round(math.degrees(cfg["recorrido"]["giro_diagonal_rad"]))),
            ("fotos tomadas", guardar.total),
            ("rosas vistas en las fotos", len(analizador.detecciones)),
            ("rosas sin repetir", len(rosas)),
            ("descartadas por pequeñas (< 32 px)", analizador.descartadas["pequenas"]),
            ("óptimas señaladas con el puntero", f"{len(avance.senaladas)} ({avance.fuera_de_alcance} fuera de "
             "alcance: el puntero quedó cerca)" if cfg["accion"]["tipo"] == "senalar" else "acción apagada"),
            ("obstáculos encontrados", "; ".join(
                f"camino {o['camino']} metro {o['x']:.1f}: {o['resultado']}" for o in avance.obstaculos) or "ninguno"),
            ("factor de color (tarjeta)", "sin calibrar"),
            ("percepción", f"candidatas {eleccion['candidatas']}, clasificador {eleccion['clasificador']}"),
            ("versión del modelo", modelo_equipo.revisar(cfg)["clasificador"]["motivo"]
             if eleccion["clasificador"] == "rosanet" else "oráculo (simulación)"),
            ("tiempo de la ronda (s)", round((hora_fin - hora_inicio).total_seconds())),
        ],
    })
    estados = {f["rosa_id"]: f["estado"] for f in rep.todas}
    resultado = metricas.comparar(rosas, escena.verdad, camas, estados)
    guardar_json(carpeta / "metricas.json", {**resultado, "descartadas": analizador.descartadas})
    mostrar_resumen(rosas, resultado, analizador)

    rutas = archivos.guardar(rep, base / "salida", cfg["reporte"]["formatos"], ya_enviados=base / "enviados")
    for o in avance.obstaculos:
        print(f"Obstáculo en el camino {o['camino']}, metro {o['x']:.1f}: {o['resultado']}")
    if rep.obstaculos:
        print(f"Cuadrantes junto a un camino bloqueado (revisados solo en parte): {', '.join(rep.obstaculos)}")
    print("  orden  cuadrante      prioridad  óptimo  mañana  inmaduro  pasado  dudosa")
    for c in sorted(rep.cuadrantes, key=lambda f: f["orden"]):
        print(f"  {c['orden']:>5}  {c['cuadrante_id']:<14} {c['prioridad']:<9}  {c['optimo']:>6}  "
              f"{c['lista_manana']:>6}  {c['inmaduro']:>8}  {c['pasado']:>6}  {c['dudosa']:>6}")
    listas = sum(f["estado"] == "optimo" for f in rep.rosas_listas)
    print(f"Reporte: {listas} para cortar hoy, {len(rep.rosas_listas) - listas} mañana, "
          f"{len(rep.dudosas)} dudosas")
    for ruta in rutas:
        print(f"  {ruta}")

    # Envío: durante la ronda no hay WiFi; aparece al volver a la base (sección 11 del plan).
    wifi = envio.ConexionSimulada(hay_wifi=False)
    bandeja, enviador, conexion = envio.crear(cfg, wifi)
    print(f"Envío en el camino: {envio.describir(bandeja.intentar(enviador, conexion))}")
    wifi.hay_wifi = True
    print(f"Envío en la base (hay WiFi): {envio.describir(bandeja.intentar(enviador, conexion))}")
    return 0


def main(argv=None) -> int:
    args = leer_argumentos(argv)
    cfg = configuracion.cargar(args.config, {
        "modo": args.modo,
        "percepcion.candidatas": args.candidatas,
        "percepcion.clasificador": args.clasificador,
        "sim.rosas": args.rosas,
        "sim.semilla": args.semilla,
    })
    print(f"Modo: {cfg['modo']}")
    reanudar = None
    if args.continuar is not None:
        import ronda
        base = configuracion.ruta(cfg["datos_dir"])
        carpeta = (ronda.ultima_sin_terminar(base) if args.continuar == "ultima"
                   else base / "rondas" / args.continuar)
        if carpeta is None or not (carpeta / "checkpoint.json").exists():
            print("ERROR: no hay una ronda a medias para continuar.")
            return 1
        avance = ronda.Avance.leer(carpeta)
        # se sigue con la misma escena con la que empezó
        cfg["sim"]["semilla"], cfg["sim"]["rosas"] = avance.datos["semilla"], avance.datos["rosas"]
        reanudar = (carpeta, avance)
    try:
        eleccion = mostrar_percepcion(cfg)
    except (RuntimeError, ValueError) as e:
        print(f"ERROR: {e}")
        return 1

    if cfg["modo"] == "real":
        print("Modo real: falta llenar cuerpo/real_backend.py con el SDK AimDK_X2 (sección 14 del plan).")
        return 0
    return correr_sim(cfg, eleccion, args, reanudar)


if __name__ == "__main__":
    sys.exit(main())
