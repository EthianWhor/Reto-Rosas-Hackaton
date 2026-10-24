"""Arranca la ronda del robot (ver PLAN_robot_rosas_X2.md).

Por ahora (paso 3) revisa qué ofrece el modelo del equipo en ml/, arma el
invernadero de prueba (2 camas de 10 m) y recorre un camino: para cada 2,5 m,
toma las 4 posturas, guarda las fotos (color + profundidad) en datos/rondas/,
encuentra y ubica cada rosa (cama, metro, altura), junta las repetidas y
compara el resultado con la verdad de la simulación.

Se corre desde la carpeta robot/:
    python main.py                     -> recorre el camino 1 y guarda las fotos
    python main.py --ventana           -> lo mismo, mirando el visor de MuJoCo
    python main.py --camino 0          -> otro camino (0 = la orilla, solo ve la cama 1)
    python main.py --revisar           -> solo revisa todo, carga la escena y toma una foto de prueba
    python main.py --rosas cartel      -> como se verá con fotos reales (usa RosaNet si está lista)
"""

import argparse
import json
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
    p.add_argument("--camino", type=int, help="Camino a recorrer (por defecto sim.camino_inicial)")
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
    from percepcion.analisis import crear_analizador
    from percepcion.dedup import juntar
    from reporte import archivos
    from reporte.tabla import armar_reporte
    from sim.escena_invernadero import CAMARA, armar_escena, resolucion

    if cfg["sim"]["rosas"] == "cartel":
        print("ERROR: las rosas con fotos reales (carteles) todavía no están hechas (sección 7.4 del plan).")
        return 1
    escena = armar_escena(cfg, args.camino)
    m, d = escena.m, escena.d
    camino = escena.plano.camino(escena.camino)
    ancho, alto = resolucion(cfg)
    print(f"Invernadero de prueba: {len(escena.plano.camas)} camas de {escena.plano.largo_m:g} m, "
          f"{len(escena.verdad)} rosas")
    print(f"Robot en el camino {camino.numero} (cama {camino.cama_izq} a la izquierda, "
          f"cama {camino.cama_der} a la derecha): {m.nu} motores")
    print(f"Cámara de la cabeza: {ancho} x {alto}, fovy {m.camera(CAMARA).fovy[0]:.1f}°")

    visor = None
    if args.ventana:
        import mujoco.viewer
        visor = mujoco.viewer.launch_passive(m, d)
    cuerpo = CuerpoSim(escena, cfg, visor)
    try:
        cuerpo.pararse()
        print(f"Cámara a {cuerpo.foto().cam_pos[2]:.2f} m del piso")
        base = configuracion.ruta(cfg["datos_dir"])
        if args.revisar:
            salida = base / "fotos" / "prueba_camara.png"
            salida.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(cuerpo.foto().rgb).save(salida)
            print(f"Foto de prueba: {salida}")
            if visor is not None:
                while visor.is_running():
                    visor.sync()
                    time.sleep(0.02)
            return 0

        analizador = crear_analizador(cfg, eleccion, escena.plano, escena.verdad)
        carpeta = ronda.nueva_carpeta(cfg, base)
        guardar = ronda.GuardarCapturas(carpeta)
        guardar_json(carpeta / "verdad.json",
                     {"semilla": cfg["sim"]["semilla"], "rosas": [r.a_dict() for r in escena.verdad]})
        inicio = time.time()
        hora_inicio = datetime.now()
        ronda.recorrer_camino(cuerpo, cfg, escena.plano, escena.camino, guardar, analizador)
        print(f"Listo: {guardar.total} fotos en {carpeta} ({time.time() - inicio:.0f} s)")

        rosas = juntar(analizador.detecciones, cfg["dedup"]["radio_m"], cfg["invernadero"]["id"])
        guardar_json(carpeta / "rosas.json", [r.a_dict() for r in rosas])
        camas = {c for c in (camino.cama_izq, camino.cama_der) if c is not None}
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
                ("caminos recorridos", f"{camino.numero} (1 de {len(escena.plano.caminos)})"),
                ("paradas cada (m)", cfg["recorrido"]["paso_entre_paradas_m"]),
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

        rutas = archivos.guardar(rep, configuracion.ruta(cfg["datos_dir"]) / "salida", cfg["reporte"]["formatos"])
        print("  orden  cuadrante      prioridad  óptimo  mañana  inmaduro  pasado  dudosa")
        for c in sorted(rep.cuadrantes, key=lambda f: f["orden"]):
            print(f"  {c['orden']:>5}  {c['cuadrante_id']:<14} {c['prioridad']:<9}  {c['optimo']:>6}  "
                  f"{c['lista_manana']:>6}  {c['inmaduro']:>8}  {c['pasado']:>6}  {c['dudosa']:>6}")
        listas = sum(f["estado"] == "optimo" for f in rep.rosas_listas)
        print(f"Reporte: {listas} para cortar hoy, {len(rep.rosas_listas) - listas} mañana, "
              f"{len(rep.dudosas)} dudosas")
        for ruta in rutas:
            print(f"  {ruta}")
    except KeyboardInterrupt:
        print("Ronda interrumpida.")
        return 1
    finally:
        cuerpo.cerrar()
        if visor is not None:
            visor.close()
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
