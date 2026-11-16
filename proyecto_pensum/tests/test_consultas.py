"""Pruebas con un pensum pequeño cuya respuesta se calcula a mano.

   A -> B -> C      (prerrequisitos)
   A -> D           (prerrequisito)
   D ~ E            (E tiene a D como correquisito)
"""
from src import consultas as q
from src.grafo import construir_grafo, validar_pensum

MATERIAS = {
    "A": {"nombre": "A", "creditos": 3, "semestre_pensum": 1, "tipo": "obligatoria"},
    "B": {"nombre": "B", "creditos": 3, "semestre_pensum": 2, "tipo": "obligatoria"},
    "C": {"nombre": "C", "creditos": 3, "semestre_pensum": 3, "tipo": "obligatoria"},
    "D": {"nombre": "D", "creditos": 4, "semestre_pensum": 2, "tipo": "obligatoria"},
    "E": {"nombre": "E", "creditos": 3, "semestre_pensum": 2, "tipo": "obligatoria"},
}
ARISTAS = [("B", "A", "prerreq"), ("C", "B", "prerreq"), ("D", "A", "prerreq"), ("E", "D", "correq")]
REGLAS = {"creditos_total": 16, "creditos_max": 20}


def grafo():
    return construir_grafo(MATERIAS, ARISTAS)


def test_bloqueadas_por_es_en_cadena():
    assert q.bloqueadas_por(grafo(), "A", {}) == ["B", "C", "D"]


def test_disponibles_sin_historial():
    assert q.disponibles(grafo(), {}) == ["A"]


def test_disponibles_tras_aprobar_a():
    assert q.disponibles(grafo(), {"A": "aprobada"}) == ["B", "D"]


def test_correquisito_cursando_habilita():
    estados = {"A": "aprobada", "D": "cursando"}
    assert "E" in q.disponibles(grafo(), estados)


def test_perder_materia_la_deja_pendiente_y_bloquea_hijas():
    estados = q.estados_actuales([("A", "1", "perdida")])
    assert q.disponibles(grafo(), estados) == ["A"]
    assert q.bloqueadas(grafo(), estados) == ["B", "C", "D", "E"]


def test_aprobar_en_reintento_gana():
    estados = q.estados_actuales([("A", "1", "perdida"), ("A", "2", "aprobada")])
    assert estados["A"] == "aprobada"


def test_creditos():
    r = q.resumen_creditos(grafo(), {"A": "aprobada", "B": "cursando"})
    assert (r["total"], r["aprobados"], r["en_curso"], r["faltantes"]) == (16, 3, 3, 10)


def test_semestres_minimos_cadena_manda():
    s = q.semestres_minimos(grafo(), {}, REGLAS)
    assert s["por_cadena"] == 3 and s["minimo"] == 3


def test_validar_detecta_ciclo():
    G = construir_grafo(MATERIAS, ARISTAS + [("A", "C", "prerreq")])
    assert any("Ciclo" in p for p in validar_pensum(G))


def test_validar_pensum_ok():
    assert validar_pensum(grafo(), REGLAS) == []
