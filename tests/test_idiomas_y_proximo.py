"""Idiomas con nivelación, lista agrupada y 'próximo semestre'."""
from pathlib import Path

from src import consultas as q
from src.carga import (cargar_intentos, cargar_materias, cargar_prerrequisitos,
                       cargar_reglas)
from src.grafo import construir_grafo

RAIZ = Path(__file__).resolve().parent.parent


def nodo(nombre, creditos, semestre, tipo):
    return {"nombre": nombre, "creditos": creditos, "semestre_pensum": semestre, "tipo": tipo}


def chico():
    materias = {
        "A": nodo("A", 3, 1, "obligatoria"),
        "B": nodo("B", 3, 2, "obligatoria"),
        "C": nodo("C", 3, 1, "obligatoria"),
        "E1": nodo("E1", 3, 1, "electiva"),
        "E2": nodo("E2", 3, 1, "electiva"),
        "L1": nodo("L1", 0, 1, "idioma"),
        "L2": nodo("L2", 0, 2, "idioma"),
        "L3": nodo("L3", 0, 3, "idioma"),
    }
    return construir_grafo(materias, [("B", "A", "prerreq")])


def test_nivelacion_cubre_los_niveles_inferiores():
    estados = q.aplicar_nivelacion_idiomas(chico(), {"L2": "aprobada"})
    assert estados["L1"] == "aprobada"


def test_solo_se_ofrece_el_siguiente_nivel_de_idiomas():
    libres = q.disponibles(chico(), {"L2": "aprobada"})
    assert [c for c in libres if c.startswith("L")] == ["L3"]


def test_si_un_nivel_se_esta_cursando_no_se_ofrece_otro():
    libres = q.disponibles(chico(), {"L1": "cursando"})
    assert [c for c in libres if c.startswith("L")] == []


def test_agrupar_separa_por_tipo():
    g = q.agrupar(chico(), ["A", "E1", "L1", "C"])
    assert g["obligatorias"] == ["A", "C"] and g["electivas"] == ["E1"] and g["idiomas"] == ["L1"]


def test_proximo_semestre_desbloquea_lo_que_depende_de_lo_que_cursas():
    G = chico()
    estados = {"A": "cursando"}
    assert "B" not in q.disponibles(G, estados)
    assert "B" in q.disponibles_proximo_semestre(G, estados)


def test_sugerir_matricula_prioriza_y_completa_con_electivas():
    reglas = {"creditos_min": 9, "creditos_max": 9}
    elegidas, total = q.sugerir_matricula(chico(), {}, reglas)
    assert elegidas == ["A", "C", "E1"] and total == 9


def _caso_real():
    base = RAIZ / "data" / "sistemas"
    G = construir_grafo(cargar_materias(base / "materias.csv"),
                        cargar_prerrequisitos(base / "prerrequisitos.csv"))
    intentos = cargar_intentos(RAIZ / "data" / "estudiantes" / "validacion_pga.csv")
    estados = q.estados_actuales([(i["codigo"], i["periodo"], i["estado"]) for i in intentos])
    return G, estados, cargar_reglas(base / "reglas.json")


def test_caso_real_idiomas_ya_cubiertos_y_solo_el_siguiente():
    G, estados, _ = _caso_real()
    idiomas = [c for c in q.disponibles(G, estados) if c.startswith("IGL")]
    assert idiomas == ["IGL1040"]


def test_caso_real_proximo_semestre():
    G, estados, reglas = _caso_real()
    ahora = set(q.disponibles(G, estados))
    proximo = set(q.disponibles_proximo_semestre(G, estados))
    nuevas = {"IST4021", "IST2110", "IST4330", "IST7072", "FIS1033"}
    assert nuevas <= proximo and not (nuevas & ahora)
    elegidas, total = q.sugerir_matricula(G, estados, reglas)
    assert reglas["creditos_min"] <= total <= reglas["creditos_max"]
