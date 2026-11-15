"""Perceptrón de clase, importancia de materias (centralidad), retiro y tope por nivel de idiomas."""
from pathlib import Path

import pytest

from src import consultas as q
from src import importancia as im
from src import perceptron as pc
from src.carga import (cargar_intentos, cargar_materias, cargar_prerrequisitos,
                       cargar_reglas)
from src.grafo import construir_grafo

RAIZ = Path(__file__).resolve().parent.parent


def pensum():
    base = RAIZ / "data" / "sistemas"
    G = construir_grafo(cargar_materias(base / "materias.csv"),
                        cargar_prerrequisitos(base / "prerrequisitos.csv"))
    intentos = cargar_intentos(RAIZ / "data" / "estudiantes" / "validacion_pga.csv")
    estados = q.estados_actuales([(i["codigo"], i["periodo"], i["estado"]) for i in intentos])
    return G, estados, cargar_reglas(base / "reglas.json")


# ---------------- perceptrón
def test_el_perceptron_reproduce_los_apuntes_del_and():
    p = pc.Perceptron(2)
    p.paso((0, 0), 0)
    assert p.sesgo == pytest.approx(0.072)
    p.paso((0, 1), 0)
    assert p.pesos == pytest.approx([0.0, -0.05]) and p.sesgo == pytest.approx(0.022)
    p.paso((1, 0), 0)
    assert p.pesos == pytest.approx([-0.05, -0.05]) and p.sesgo == pytest.approx(-0.028)


def test_el_perceptron_aprende_el_and():
    p = pc.Perceptron(2)
    _, errores = p.entrenar(pc.AND)
    assert errores == 0 and all(p.predecir(x) == y for x, y in pc.AND)


def test_perceptron_con_datos_simulados_supera_al_modelo_trivial():
    datos = pc.filas_a_datos(pc.generar_datos_simulados())
    r = pc.evaluar(datos)
    assert r["exactitud_test"] > r["exactitud_base"] and r["modelo"].pesos[0] > 0
    assert 2.5 <= pc.umbral_nota(r["modelo"]) <= 4.0


def test_etiqueta_aprueba_desde_3_0():
    datos = pc.filas_a_datos([{"nota_origen": 4, "nota_destino": 3.0}, {"nota_origen": 2, "nota_destino": 2.9}])
    assert [y for _, y in datos] == [1, 0]


# ---------------- importancia
def test_medidas_de_calculo_2():
    G, _, _ = pensum()
    M = im.medidas(G)
    assert M["MAT1111"]["dependientes"] == 4 and M["MAT1111"]["descendientes"] == 7


def test_puntaje_entre_0_y_1_y_materias_criticas_arriba():
    G, _, reglas = pensum()
    p = im.puntaje(G, reglas["pesos_importancia"])
    assert all(0 <= x <= 1 for x in p.values())
    top5 = [c for c, _ in im.ranking(G, reglas["pesos_importancia"])[:5]]
    assert "IST2088" in top5 and p["IST2088"] > p["MAT4021"]


def test_la_dificultad_cambia_el_puntaje_si_tiene_peso():
    G, _, reglas = pensum()
    pesos = dict(reglas["pesos_importancia"], dificultad=0.5)
    sin = im.puntaje(G, pesos)
    con = im.puntaje(G, pesos, {"MAT4021": 5.0})
    assert con["MAT4021"] > sin["MAT4021"]


# ---------------- retiro
def test_retiro_permitido_en_el_caso_real():
    G, estados, reglas = pensum()
    ok, mensaje = q.puede_retirar(G, estados, "IST2089", reglas)
    assert ok and "10 créditos" in mensaje


def test_no_se_puede_retirar_si_se_baja_del_minimo():
    G, _, reglas = pensum()
    estados = {"FIS1023": "cursando", "IST2089": "cursando"}  # 4 + 3 = 7 créditos
    ok, mensaje = q.puede_retirar(G, estados, "IST2089", reglas)
    assert not ok and "mínimo es 7" in mensaje


def test_no_se_retira_lo_que_no_se_cursa():
    G, estados, reglas = pensum()
    assert not q.puede_retirar(G, estados, "MAT1101", reglas)[0]


# ---------------- idiomas limitan hasta qué semestre se ofrece
def _chico():
    nodo = lambda s, t, c=3: {"nombre": "x", "creditos": c, "semestre_pensum": s, "tipo": t}
    materias = {f"M{i}": nodo(i, "obligatoria") for i in range(1, 6)}
    materias.update({f"L{i}": nodo(i, "idioma", 0) for i in range(1, 4)})
    return construir_grafo(materias, [])


def test_tope_por_nivel_de_idiomas_solo_si_esta_activado():
    G = _chico()
    estados = {"L1": "aprobada"}
    assert q.ventana_matricula(G, estados, {"ventana_semestres": 3}) == (1, 3)
    assert q.ventana_matricula(G, estados, {"ventana_semestres": 3, "idiomas_semestres_adelante": 1}) == (1, 2)
    estados = {"L2": "aprobada"}
    assert q.ventana_matricula(G, estados, {"ventana_semestres": 3, "idiomas_semestres_adelante": 1}) == (1, 3)
