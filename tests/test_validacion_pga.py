"""Validación con un caso real de resultado conocido.

Historial anónimo de un estudiante de Sistemas (dos semestres cerrados y uno en curso).
La app oficial de la universidad reporta un Promedio General Acumulado (PGA) de 3.70
(la propia app aclara que sus notas son una guía y no oficiales).
"""
from pathlib import Path

import pytest

from src import consultas as q
from src import promedio as pr
from src.carga import (cargar_intentos, cargar_materias, cargar_prerrequisitos,
                       cargar_reglas)
from src.grafo import construir_grafo

RAIZ = Path(__file__).resolve().parent.parent
PGA_APP = 3.70


def cargar():
    base = RAIZ / "data" / "sistemas"
    G = construir_grafo(cargar_materias(base / "materias.csv"),
                        cargar_prerrequisitos(base / "prerrequisitos.csv"))
    intentos = cargar_intentos(RAIZ / "data" / "estudiantes" / "validacion_pga.csv")
    return G, intentos, cargar_reglas(base / "reglas.json")


def test_reproduce_el_pga_de_la_app():
    G, intentos, reglas = cargar()
    assert pr.promedio(G, intentos, reglas["politica_repetidas"]) == pytest.approx(PGA_APP, abs=0.005)


def test_la_politica_de_ultimo_intento_no_coincide():
    G, intentos, _ = cargar()
    assert pr.promedio(G, intentos, "ultima") == pytest.approx(3.85, abs=0.005)


def test_las_retiradas_no_afectan_el_promedio():
    G, intentos, reglas = cargar()
    sin_retiradas = [i for i in intentos if i["estado"] != "retirada"]
    politica = reglas["politica_repetidas"]
    assert pr.promedio(G, intentos, politica) == pytest.approx(pr.promedio(G, sin_retiradas, politica))


def test_notas_coherentes_con_el_estado():
    _, intentos, reglas = cargar()
    assert pr.validar_notas(intentos, reglas["nota_aprobatoria"]) == []


def test_creditos_del_caso():
    G, intentos, _ = cargar()
    estados = q.estados_actuales([(i["codigo"], i["periodo"], i["estado"]) for i in intentos])
    r = q.resumen_creditos(G, estados)
    assert (r["aprobados"], r["en_curso"]) == (24, 13)
