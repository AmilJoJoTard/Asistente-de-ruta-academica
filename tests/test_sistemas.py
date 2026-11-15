"""Pruebas con el pensum real de Sistemas (sirven mientras se completan los prerrequisitos)."""
from pathlib import Path

from src import consultas as q
from src.carga import cargar_materias, cargar_prerrequisitos, cargar_reglas
from src.grafo import construir_grafo, validar_pensum

BASE = Path(__file__).resolve().parent.parent / "data" / "sistemas"


def pensum():
    G = construir_grafo(
        cargar_materias(BASE / "materias.csv"), cargar_prerrequisitos(BASE / "prerrequisitos.csv")
    )
    return G, cargar_reglas(BASE / "reglas.json")


def test_pensum_valido_y_suma_155():
    G, reglas = pensum()
    assert validar_pensum(G, reglas) == []


def test_retirar_calculo_2_bloquea_en_cadena():
    G, _ = pensum()
    afectadas = set(q.bloqueadas_por(G, "MAT1111", {}))
    assert {"MAT1121", "MAT4011", "FIS1043", "EST7042"} <= afectadas


def test_matematicas_discretas_sin_prerrequisitos():
    G, _ = pensum()
    assert list(G.in_edges("MAT4021")) == []


def test_calculo_2_exige_fisica_mecanica_como_correq():
    G, _ = pensum()
    base = {"MAT1101": "aprobada"}
    assert not q.es_disponible(G, base, "MAT1111")
    assert q.es_disponible(G, {**base, "FIS1023": "cursando"}, "MAT1111")


def _requisitos(G, codigo):
    return {u for u, _ in G.in_edges(codigo)}


def test_requisitos_confirmados_semestres_vi_a_x():
    G, _ = pensum()
    assert _requisitos(G, "IST7410") == {"IST2110", "IST4031"}
    assert _requisitos(G, "IST70811") == {"IST4012"}
    assert _requisitos(G, "IST7111") == {"IST4310"}
    assert _requisitos(G, "IST7121") == {"IST7111"}
    assert _requisitos(G, "IST7420") == {"EST7042", "IST4360"}
    assert _requisitos(G, "IST4360") == {"IST2088", "MAT4011"}
    assert _requisitos(G, "IIN4319") == set()
    assert _requisitos(G, "IST7191") == set()


def test_pensum_completo_necesita_al_menos_9_semestres():
    G, reglas = pensum()
    s = q.semestres_minimos(G, {}, reglas)
    assert s["por_cadena"] == 9
    assert s["minimo"] >= 9


def test_correcciones_confirmadas_por_el_estudiante():
    G, _ = pensum()
    assert _requisitos(G, "FIS1033") == {"FIS1023", "MAT1101"}
    assert _requisitos(G, "IST7072") == {"MAT4021"}
    assert _requisitos(G, "ELG1302") == {"IST7191"}


def test_calculo_3_exige_calculo_2_y_algebra_lineal():
    G, _ = pensum()
    assert _requisitos(G, "MAT1121") == {"MAT1111", "MAT1031"}


def test_seminarios_sin_prerrequisitos_y_codigos_confirmados():
    G, _ = pensum()
    assert _requisitos(G, "IST4370") == set() and _requisitos(G, "IST4380") == set()
    assert {"FIS1033", "FIS1043", "IST70811"} <= set(G.nodes)
