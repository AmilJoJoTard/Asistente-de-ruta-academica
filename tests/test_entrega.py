"""Modo demo y herramientas de la prueba piloto."""
from pathlib import Path

import pytest

from src import consultas as q
from src import medicion as md
from src.carga import (cargar_intentos, cargar_materias, cargar_prerrequisitos,
                       cargar_reglas)
from src.cli import main
from src.grafo import construir_grafo

RAIZ = Path(__file__).resolve().parent.parent


def caso_real():
    base = RAIZ / "data" / "sistemas"
    G = construir_grafo(cargar_materias(base / "materias.csv"),
                        cargar_prerrequisitos(base / "prerrequisitos.csv"))
    intentos = cargar_intentos(RAIZ / "data" / "estudiantes" / "validacion_pga.csv")
    estados = q.estados_actuales([(i["codigo"], i["periodo"], i["estado"]) for i in intentos])
    return G, estados, intentos, cargar_reglas(base / "reglas.json")


def test_claves_de_la_medicion():
    G, estados, intentos, reglas = caso_real()
    k = md.claves(G, estados, intentos, reglas)
    assert k["A"][0] == "24 créditos aprobados" and k["A"][1].startswith("7 materias") and k["A"][2] == "promedio 3.53"
    assert k["B"][0].startswith("118 créditos") and k["B"][1].startswith("9 materias") and k["B"][2] == "promedio 3.42"


def test_analisis_de_la_medicion():
    filas = [{"participante": "P1", "condicion": "manual", "tiempo_seg": 600, "correctas": 2},
             {"participante": "P2", "condicion": "manual", "tiempo_seg": 700, "correctas": 1},
             {"participante": "P1", "condicion": "programa", "tiempo_seg": 120, "correctas": 3},
             {"participante": "P2", "condicion": "programa", "tiempo_seg": 100, "correctas": 3}]
    r = md.analizar(filas)
    assert r["manual"]["tiempo_medio"] == pytest.approx(650) and r["programa"]["tiempo_medio"] == pytest.approx(110)
    assert r["manual"]["exactitud"] == pytest.approx(0.5) and r["programa"]["exactitud"] == pytest.approx(1.0)
    texto = md.texto_analisis(filas)
    assert "83 % menos" in texto and r"\begin{tabular}" in texto


def test_analisis_pide_las_dos_condiciones():
    assert "Faltan" in md.texto_analisis([{"participante": "P1", "condicion": "manual", "tiempo_seg": 1, "correctas": 1}])


def test_modo_demo_recorre_todo(capsys):
    main(["--demo"])
    salida = capsys.readouterr().out
    assert "Promedio acumulado: 3.70" in salida and "Materias más críticas" in salida
    assert "coincide con el programa" in salida and "No: no puedes matricular Cálculo III" in salida
