"""Arranca la ronda del robot (ver PLAN_robot_rosas_X2.md).

Revisa qué ofrece el modelo del equipo en ml/, arma el invernadero de prueba
(2 camas de 10 m) y recorre todos sus caminos: para cada 1,25 m,
toma las 4 posturas, guarda las fotos (color + profundidad) en datos/rondas/,
encuentra y ubica cada rosa (cama, metro, altura), junta las repetidas,
compara el resultado con la verdad de la simulación, arma el reporte Excel +
JSON y lo envía al dashboard cuando "aparece" el WiFi al volver a la base.

Se corre desde la carpeta robot/:
    python main.py                     -> ronda por todos los caminos, reporte y envío
    python main.py --ventana           -> lo mismo, mirando el visor de MuJoCo
    python main.py --camino 1          -> solo un camino (0 = la orilla, solo ve la cama 1)
    python main.py --revisar           -> solo revisa todo, carga la escena y toma una foto de prueba
    python main.py --rosas cartel      -> como se verá con fotos reales (usa RosaNet si está lista)
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


def mostrar_resumen(rosas, resultado: dict, analizador) -> None:
    print(f"Rosas: {len(analizador.detecciones)} vistas en las fotos → {len(rosas)} sin repetir")
    print("Métricas contra la verdad:")
    for clave, valor in resultado.items():
        print(f"  {clave}: {valor}")
    print(f"  descartadas: {analizador.descartadas}")


def correr_sim(cfg: dict, eleccion: dict, args: argparse.Namespace) -> int:
    from PIL import Image

    import metricas
    import ronda
    from cuerpo.sim_backend import CuerpoSim
    from navegacion.plano import armar_plano
    from percepcion.analisis import crear_analizador
    from percepcion.dedup import juntar
    from reporte import archivos, envio
    from reporte.tabla import armar_reporte
    from sim.escena_invernadero import CAMARA, armar_escena, resolucion

    caminos = [args.camino] if args.camino is not None else (
        cfg["sim"]["caminos"] or [c.numero for c in armar_plano(cfg).caminos])
    escena = armar_escena(cfg, caminos[0])
    m = escena.m
    ancho, alto = resolucion(cfg)
    print(f"Invernadero de prueba: {len(escena.plano.camas)} camas de {escena.plano.largo_m:g} m, "
          f"{len(escena.verdad)} rosas")
    print(f"Ronda por los caminos {caminos}: así cada cama se ve por sus dos lados")
    print(f"Cámara de la cabeza: {ancho} x {alto}, fovy {m.camera(CAMARA).fovy[0]:.1f}°, "
          f"giro de las fotos {math.degrees(cfg['recorrido']['giro_diagonal_rad']):.0f}°")
    base = configuracion.ruta(cfg["datos_dir"])

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
    carpeta = ronda.nueva_carpeta(cfg, base)
    guardar = ronda.GuardarCapturas(carpeta)
    guardar_json(carpeta / "verdad.json",
                 {"semilla": cfg["sim"]["semilla"], "rosas": [r.a_dict() for r in escena.verdad]})
    inicio = time.time()
    hora_inicio = datetime.now()
    camas: set[int] = set()
    try:
        for i, numero in enumerate(caminos):
            if i > 0:
                # En la simulación el robot aparece en la entrada del siguiente camino.
                # La ruta en serpiente (salir por el fondo y entrar al siguiente) llega después.
                escena = armar_escena(cfg, numero)
            camino = escena.plano.camino(numero)
            camas |= {c for c in (camino.cama_izq, camino.cama_der) if c is not None}
            print(f"Camino {numero}: cama {camino.cama_izq} a la izquierda, cama {camino.cama_der} a la derecha")
            visor = None
            if args.ventana:
                import mujoco.viewer
                visor = mujoco.viewer.launch_passive(escena.m, escena.d)
            cuerpo = CuerpoSim(escena, cfg, visor)
            try:
                cuerpo.pararse()
                ronda.recorrer_camino(cuerpo, cfg, escena.plano, numero, guardar, analizador)
            finally:
                cuerpo.cerrar()
                if visor is not None:
                    visor.close()
    except KeyboardInterrupt:
        print("Ronda interrumpida.")
        return 1
    print(f"Listo: {guardar.total} fotos en {carpeta} ({time.time() - inicio:.0f} s)")

    rosas = juntar(analizador.detecciones, cfg["dedup"]["radio_m"], cfg["invernadero"]["id"])
    guardar_json(carpeta / "rosas.json", [r.a_dict() for r in rosas])
    hora_fin = datetime.now()
    rep = armar_reporte(rosas, escena.plano, camas, cfg, {
        "id_ronda": carpeta.name,
        "inicio": f"{hora_inicio:%Y-%m-%d %H:%M:%S}",
        "fin": f"{hora_fin:%Y-%m-%d %H:%M:%S}",
        "fechas_fotos": guardar.fechas,
        "ronda": [
            ("id_ronda", carpeta.name),
            ("modo", cfg["modo"]),
            ("inicio / fin", f"{hora_inicio:%Y-%m-%d %H:%M:%S} / {hora_fin:%Y-%m-%d %H:%M:%S}"),
            ("caminos recorridos", f"{len(caminos)} de {len(escena.plano.caminos)}: {caminos}"),
            ("paradas cada (m)", cfg["recorrido"]["paso_entre_paradas_m"]),
            ("giro de las fotos (°)", round(math.degrees(cfg["recorrido"]["giro_diagonal_rad"]))),
            ("fotos tomadas", guardar.total),
            ("rosas vistas en las fotos", len(analizador.detecciones)),
            ("rosas sin repetir", len(rosas)),
            ("descartadas por pequeñas (< 32 px)", analizador.descartadas["pequenas"]),
            ("obstáculos encontrados", 0),
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
    try:
        eleccion = mostrar_percepcion(cfg)
    except (RuntimeError, ValueError) as e:
        print(f"ERROR: {e}")
        return 1

    if cfg["modo"] == "real":
        print("Modo real: falta llenar cuerpo/real_backend.py con el SDK AimDK_X2 (sección 14 del plan).")
        return 0
    return correr_sim(cfg, eleccion, args)


if __name__ == "__main__":
    sys.exit(main())
