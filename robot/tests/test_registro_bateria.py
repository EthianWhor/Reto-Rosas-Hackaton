"""Log de la ronda en archivo y vuelta a la base por batería (sección 15 del plan)."""

import re
import sys

import pytest

import configuracion
import registro
import ronda
from navegacion.plano import armar_plano
from navegacion.ruta import paradas


def test_el_log_guarda_todo_con_la_hora(tmp_path):
    with registro.Bitacora(tmp_path / "logs") as b:
        print("Modelo del equipo: listo")                 # antes de saber la ronda: queda en memoria
        registro.abrir_log(tmp_path / "logs" / "ronda_X.log")
        print("camino 1 →, parada x = 0.0 m", end="")
        print(": 4 fotos")
        assert sys.stdout is b
    assert sys.stdout is not b                             # devuelve la pantalla al salir
    lineas = (tmp_path / "logs" / "ronda_X.log").read_text(encoding="utf-8").splitlines()
    assert len(lineas) == 2 and all(re.match(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d  ", l) for l in lineas)
    assert lineas[0].endswith("Modelo del equipo: listo") and lineas[1].endswith("0.0 m: 4 fotos")


def test_si_se_cae_el_error_queda_en_el_log(tmp_path):
    with pytest.raises(ZeroDivisionError):
        with registro.Bitacora(tmp_path / "logs"):
            print("arrancando")
            1 / 0
    (log,) = (tmp_path / "logs").glob("error_*.log")       # todavía no había ronda: log de error aparte
    texto = log.read_text(encoding="utf-8")
    assert "arrancando" in texto and "ZeroDivisionError" in texto


class SinBateria:
    def nivel_bateria(self):
        return None


def test_sin_lectura_de_bateria_no_vuelve(tmp_path):
    cfg = configuracion.cargar()
    assert not ronda.bateria_baja(SinBateria(), cfg, ronda.Avance.nuevo(tmp_path, cfg, [0]))


def test_vuelve_a_la_base_por_bateria_y_despues_sigue(tmp_path):
    pytest.importorskip("mujoco")
    from cuerpo.sim_backend import CuerpoSim
    from sim.escena_invernadero import armar_escena

    cfg = configuracion.cargar(cambios={"sim.largo_cama_m": 5, "sim.obstaculos": [], "accion.tipo": "ninguna",
                                        "sim.bateria.inicial_pct": 27, "recorrido.bateria_min_pct": 25})
    plano = armar_plano(cfg)
    carpeta = tmp_path / "rondas" / "x"
    carpeta.mkdir(parents=True)
    avance = ronda.Avance.nuevo(carpeta, cfg, [0, 1, 2])
    total = 3 * len(paradas(plano, cfg))

    def una_vuelta(cfg):
        escena = armar_escena(cfg, en_base=True)
        cuerpo = CuerpoSim(escena, cfg)
        try:
            cuerpo.pararse()
            completa = ronda.recorrer(cuerpo, cfg, plano, ronda.GuardarCapturas(carpeta), avance,
                                      avisar=lambda s: None)
            return completa, cuerpo.posicion()
        finally:
            cuerpo.cerrar()

    completa, donde = una_vuelta(cfg)
    assert not completa and donde == pytest.approx(tuple(cfg["sim"]["base_xy"]))   # volvió a la base
    hechas = len(avance.datos["hechas"])
    assert 0 < hechas < total
    assert ronda.Avance.leer(carpeta).datos["bateria_pct"] < 25                     # quedó anotado
    cfg["sim"]["bateria"]["inicial_pct"] = 100                                      # cargó en la base
    completa, _ = una_vuelta(cfg)
    assert completa and len(avance.datos["hechas"]) == total                        # terminó lo que faltaba
