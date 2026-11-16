"""Álgebra booleana de la matrícula: expresiones, simplificación, De Morgan y equivalencia lógica."""
from itertools import product
from pathlib import Path

import pytest

from src import booleano as bo
from src import consultas as q
from src.carga import (cargar_intentos, cargar_materias, cargar_prerrequisitos,
                       cargar_reglas)
from src.grafo import construir_grafo

RAIZ = Path(__file__).resolve().parent.parent


def pensum():
    base = RAIZ / "data" / "sistemas"
    G = construir_grafo(cargar_materias(base / "materias.csv"),
                        cargar_prerrequisitos(base / "prerrequisitos.csv"))
    return G, cargar_reglas(base / "reglas.json")


def caso_real():
    G, reglas = pensum()
    intentos = cargar_intentos(RAIZ / "data" / "estudiantes" / "validacion_pga.csv")
    estados = q.estados_actuales([(i["codigo"], i["periodo"], i["estado"]) for i in intentos])
    return G, estados, reglas


def test_expresion_de_calculo_2():
    G, _ = pensum()
    assert bo.expresion_requisitos(G, "MAT1111") == "A_MAT1101 · (A_FIS1023 + C_FIS1023)"
    assert bo.expresion_disponible(G, "MAT1111") == (
        "¬A_MAT1111 · ¬C_MAT1111 · A_MAT1101 · (A_FIS1023 + C_FIS1023)")


def test_de_morgan_de_calculo_2():
    G, _ = pensum()
    assert bo.negacion_requisitos(G, "MAT1111") == "¬A_MAT1101 + ¬A_FIS1023 · ¬C_FIS1023"


def test_minterminos_y_dont_cares_de_calculo_2():
    G, _ = pensum()
    variables, unos, dc = bo.funcion_requisitos(G, "MAT1111")
    assert variables == ["A_MAT1101", "A_FIS1023", "C_FIS1023"]
    assert unos == [5, 6] and dc == [3, 7]  # aprobada y cursando a la vez no puede ocurrir


def test_simplificacion_usa_los_dont_cares():
    G, _ = pensum()
    variables, unos, dc = bo.funcion_requisitos(G, "MAT1111")
    implicantes = bo.minimizar(len(variables), unos, dc)
    assert implicantes == ["1-1", "11-"]  # sin los X habría que escribir los mintérminos completos
    assert bo.sop_texto(variables, implicantes) == "A_MAT1101 · C_FIS1023 + A_MAT1101 · A_FIS1023"


def test_materia_sin_requisitos_es_tautologia():
    G, _ = pensum()
    assert bo.expresion_requisitos(G, "MAT4021") == "1"
    assert "tautología" in bo.texto_booleano(G, "MAT4021")


def test_la_suma_de_productos_minima_equivale_a_la_funcion():
    G, _ = pensum()
    for v in G.nodes:
        variables, unos, dc = bo.funcion_requisitos(G, v)
        n = len(variables)
        if n == 0:
            continue
        implicantes = bo.minimizar(n, unos, dc)
        for m in range(2 ** n):
            if m in dc:
                continue
            bits = format(m, f"0{n}b")
            cubierto = any(all(i == "-" or i == b for i, b in zip(imp, bits)) for imp in implicantes)
            assert cubierto == (m in unos), (v, m)


def test_la_logica_booleana_equivale_al_programa_en_todo_el_plan():
    G, _ = pensum()
    materias, combinaciones, fallos = bo.verificar_equivalencia(G)
    assert materias == G.number_of_nodes() and combinaciones > 10000 and fallos == []


def test_mapa_de_karnaugh_marca_los_dont_cares():
    G, _ = pensum()
    variables, unos, dc = bo.funcion_requisitos(G, "MAT1111")
    mapa = bo.mapa_karnaugh(variables, unos, dc)
    assert "X" in mapa and mapa.count("1") >= 2


def test_si_no_con_razones_en_el_caso_real():
    G, estados, reglas = caso_real()
    puede, razones = bo.explicar(G, estados, "MAT1111", reglas)
    assert puede and razones == []
    puede, razones = bo.explicar(G, estados, "MAT1121", reglas)
    assert not puede and any("MAT1111" in r for r in razones)


def test_explica_ventana_y_materia_ya_aprobada():
    G, estados, reglas = caso_real()
    puede, razones = bo.explicar(G, estados, "IST7191", reglas)  # Redes: sin requisitos, pero semestre 6
    assert not puede and any("ventana" in r for r in razones)
    puede, razones = bo.explicar(G, estados, "MAT1101", reglas)  # ya aprobada
    assert not puede and any("ya la aprobaste" in r for r in razones)


def test_idiomas_solo_el_siguiente_nivel():
    G, estados, reglas = caso_real()
    assert bo.explicar(G, estados, "IGL1040", reglas)[0]
    puede, razones = bo.explicar(G, estados, "IGL4040", reglas)
    assert not puede and any("siguiente nivel" in r for r in razones)
