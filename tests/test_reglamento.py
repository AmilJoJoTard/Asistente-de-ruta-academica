"""Reglas del Reglamento de Estudiantes: ventana de semestres, carga, nota mínima y estado académico."""
from pathlib import Path

import pytest

from src import consultas as q
from src import promedio as pr
from src.carga import (cargar_intentos, cargar_materias, cargar_prerrequisitos,
                       cargar_reglas)
from src.grafo import construir_grafo

RAIZ = Path(__file__).resolve().parent.parent


def caso_real():
    base = RAIZ / "data" / "sistemas"
    G = construir_grafo(cargar_materias(base / "materias.csv"),
                        cargar_prerrequisitos(base / "prerrequisitos.csv"))
    intentos = cargar_intentos(RAIZ / "data" / "estudiantes" / "validacion_pga.csv")
    estados = q.estados_actuales([(i["codigo"], i["periodo"], i["estado"]) for i in intentos])
    return G, intentos, estados, cargar_reglas(base / "reglas.json")


def test_reglas_de_ingenierias():
    _, _, _, reglas = caso_real()
    assert (reglas["creditos_min"], reglas["creditos_max"]) == (7, 17)
    assert reglas["nota_aprobatoria"] == 3.0 and reglas["nota_minima_definitiva"] == 1.5
    assert reglas["promedio_minimo"] == 3.25


def test_ventana_empieza_en_la_materia_mas_atrasada():
    G, _, estados, reglas = caso_real()
    assert q.ventana_matricula(G, estados, reglas) == (2, 4)


def test_ventana_deja_solo_calculo_2_ahora():
    G, _, estados, reglas = caso_real()
    obligatorias = [c for c in q.disponibles_matricula(G, estados, reglas)
                    if G.nodes[c]["tipo"] == "obligatoria"]
    assert obligatorias == ["MAT1111"]


def test_proximo_semestre_respeta_la_ventana():
    G, _, estados, reglas = caso_real()
    proximo = set(q.matricula_proximo_semestre(G, estados, reglas))
    obligatorias = {c for c in proximo if G.nodes[c]["tipo"] == "obligatoria"}
    assert obligatorias == {"MAT1111", "FIS1033", "IST4021", "IST2110"}
    assert "IST4330" not in proximo and "IST7072" not in proximo  # semestre 5, fuera de la ventana


def test_sugerencia_respeta_el_maximo_de_creditos():
    G, _, estados, reglas = caso_real()
    elegidas, total = q.sugerir_matricula(G, estados, reglas)
    assert total == 14 and reglas["creditos_min"] <= total <= reglas["creditos_max"]
    assert elegidas[0] == "MAT1111"  # la más atrasada del plan va primero


@pytest.mark.parametrize("promedio,creditos,esperado", [
    (3.70, 27, "normal"),
    (3.96, 16, "distinguido"),
    (3.96, 10, "normal"),
    (3.20, 27, "por debajo del mínimo (período de prueba)"),
])
def test_estado_academico(promedio, creditos, esperado):
    _, _, _, reglas = caso_real()
    assert pr.estado_academico(promedio, creditos, reglas) == esperado


def test_perder_una_materia_en_el_caso_real_mantiene_el_estado_normal():
    G, intentos, _, reglas = caso_real()
    nuevo, estado = pr.simular_perdida(G, intentos, "IST2089", reglas["nota_minima_definitiva"], reglas)
    assert nuevo == pytest.approx(104.4 / 30) and estado == "normal"
