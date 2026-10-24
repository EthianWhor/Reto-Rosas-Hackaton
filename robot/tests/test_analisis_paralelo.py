"""Análisis de las fotos en otro hilo mientras el robot sigue (sección 8 del plan)."""

import json
import threading

import pytest

import ronda


class AnalizadorFalso:
    """Devuelve una "rosa" por foto. Con `freno`, no termina hasta que se suelte (como un modelo lento)."""

    def __init__(self, freno: threading.Event | None = None, falla_en: str | None = None):
        self.freno, self.falla_en = freno, falla_en

    def analizar(self, cap, foto, camino):
        if self.freno is not None:
            self.freno.wait(5)
        if foto == self.falla_en:
            raise ValueError("el modelo falló")
        return [Rosa(foto)]


class Rosa:
    def __init__(self, foto):
        self.foto = foto

    def a_dict(self):
        return {"foto": self.foto}


def entregar(analisis, parada, fotos=2):
    for k in range(fotos):
        analisis.foto(None, f"p{parada}_{k}", 1)
    analisis.fin_parada((1, float(parada), 1))


@pytest.mark.parametrize("en_paralelo", [True, False])
def test_mismo_resultado_en_paralelo_o_no(tmp_path, en_paralelo):
    analisis = ronda.AnalisisEnParalelo(AnalizadorFalso(), tmp_path, en_paralelo)
    for p in range(3):
        entregar(analisis, p)
    assert [r.foto for r in analisis.resultado((1, 1.0, 1))] == ["p1_0", "p1_1"]
    assert analisis.esperar_todo() == [(1, 0.0, 1), (1, 1.0, 1), (1, 2.0, 1)]   # en orden
    analisis.cerrar()
    lineas = (tmp_path / "detecciones.jsonl").read_text(encoding="utf-8").splitlines()
    assert [json.loads(l)["foto"] for l in lineas] == [f"p{p}_{k}" for p in range(3) for k in range(2)]


def test_la_parada_se_marca_recien_cuando_se_analizo(tmp_path):
    freno = threading.Event()
    analisis = ronda.AnalisisEnParalelo(AnalizadorFalso(freno), tmp_path)
    entregar(analisis, 0)                     # el robot ya siguió; el modelo todavía piensa
    assert analisis.listas() == []            # si se corta aquí, la parada no queda como hecha
    freno.set()
    assert analisis.esperar_todo() == [(1, 0.0, 1)]
    analisis.cerrar()


def test_un_error_del_modelo_llega_al_robot(tmp_path):
    analisis = ronda.AnalisisEnParalelo(AnalizadorFalso(falla_en="p0_1"), tmp_path)
    entregar(analisis, 0)
    with pytest.raises(RuntimeError, match="falló el análisis") as error:
        analisis.resultado((1, 0.0, 1))
    assert isinstance(error.value.__cause__, ValueError)
    with pytest.raises(RuntimeError):
        analisis.foto(None, "otra", 1)        # no sigue como si nada
    analisis.fin_parada((1, 5.0, 1))          # una parada entregada después del error
    with pytest.raises(RuntimeError):
        analisis.resultado((1, 5.0, 1))       # avisa el error en vez de quedarse esperando
    analisis.cerrar()
