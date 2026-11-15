"""Pruebas del promedio con cuentas hechas a mano."""
import pytest

from src import promedio as pr
from src.grafo import construir_grafo

MATERIAS = {
    "A": {"nombre": "A", "creditos": 3, "semestre_pensum": 1, "tipo": "obligatoria"},
    "B": {"nombre": "B", "creditos": 3, "semestre_pensum": 1, "tipo": "obligatoria"},
    "C": {"nombre": "C", "creditos": 3, "semestre_pensum": 2, "tipo": "obligatoria"},
    "D": {"nombre": "D", "creditos": 4, "semestre_pensum": 2, "tipo": "obligatoria"},
}


def g():
    return construir_grafo(MATERIAS, [])


def intento(codigo, estado, nota=None, periodo="1"):
    return {"codigo": codigo, "periodo": periodo, "estado": estado, "nota": nota}


BASE = [
    intento("A", "aprobada", 4.0),
    intento("B", "perdida", 2.0),
    intento("D", "retirada"),
    intento("C", "cursando"),
]


def test_promedio_ignora_retiradas_y_cursando():
    # (4.0*3 + 2.0*3) / 6 = 3.0
    assert pr.promedio(g(), BASE) == pytest.approx(3.0)


def test_perder_una_materia_baja_el_promedio():
    # (12 + 6 + 0*4) / 10 = 1.8
    assert pr.promedio_si_agrego(g(), BASE, "D", 0.0) == pytest.approx(1.8)


def test_retirar_no_cambia_el_promedio():
    con_retiro = BASE + [intento("C", "retirada", periodo="2")]
    assert pr.promedio(g(), con_retiro) == pytest.approx(pr.promedio(g(), BASE))


def test_politica_repetidas():
    rep = BASE + [intento("B", "aprobada", 3.5, periodo="2")]
    assert pr.promedio(g(), rep, "todas") == pytest.approx(28.5 / 9)
    assert pr.promedio(g(), rep, "ultima") == pytest.approx(22.5 / 6)


def test_nota_necesaria():
    # (3.5 * (6 + 3) - 18) / 3 = 4.5
    assert pr.nota_necesaria(g(), BASE, "C", 3.5) == pytest.approx(4.5)


def test_nota_necesaria_imposible_y_innecesaria():
    assert pr.nota_necesaria(g(), BASE, "C", 5.0) > 5
    assert pr.nota_necesaria(g(), BASE, "C", 1.0) == 0.0


def test_sin_notas_no_hay_promedio():
    assert pr.promedio(g(), [intento("A", "cursando")]) is None


def test_validar_notas_detecta_contradicciones():
    avisos = pr.validar_notas([intento("A", "aprobada", 2.5), intento("B", "perdida", 3.2)], 3.0)
    assert len(avisos) == 2
