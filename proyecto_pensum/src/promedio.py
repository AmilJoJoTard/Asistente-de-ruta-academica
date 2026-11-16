"""Promedio ponderado por créditos y simulaciones.

Reglas del modelo (configurables en reglas.json):
- Las materias retiradas y las que se están cursando NO entran al promedio.
- Las aprobadas y las perdidas SÍ entran, con su nota, ponderadas por créditos.
- 'politica_repetidas': "todas" (cada intento cuenta) o "ultima" (solo el último intento
  de cada materia). Hay que confirmar con el reglamento cuál aplica.
"""
CUENTAN = ("aprobada", "perdida")


def intentos_que_cuentan(intentos, politica="todas"):
    validos = [i for i in intentos if i["estado"] in CUENTAN and i["nota"] is not None]
    if politica == "ultima":
        ultimo = {}
        for i in validos:
            ultimo[i["codigo"]] = i
        return list(ultimo.values())
    return validos


def _creditos(G, codigo):
    return G.nodes[codigo]["creditos"]


def _suma_y_creditos(G, cuentan):
    suma = sum(i["nota"] * _creditos(G, i["codigo"]) for i in cuentan)
    creditos = sum(_creditos(G, i["codigo"]) for i in cuentan)
    return suma, creditos


def promedio(G, intentos, politica="todas"):
    """Promedio ponderado por créditos, o None si todavía no hay notas que cuenten."""
    suma, creditos = _suma_y_creditos(G, intentos_que_cuentan(intentos, politica))
    return suma / creditos if creditos else None


def promedio_si_agrego(G, intentos, codigo, nota, estado="perdida", politica="todas"):
    """Promedio hipotético si se agrega un intento de 'codigo' con 'nota'."""
    extra = {"codigo": codigo, "periodo": "hipotetico", "estado": estado, "nota": nota}
    return promedio(G, intentos + [extra], politica)


def nota_necesaria(G, intentos, codigo, objetivo, politica="todas"):
    """Nota mínima en 'codigo' para que el promedio llegue a 'objetivo'.

    Devuelve 0.0 si ya alcanza, un número mayor a 5 si es imposible, y None si la
    materia no tiene créditos (no pesa en el promedio).
    """
    c = _creditos(G, codigo)
    if c == 0:
        return None
    base = intentos_que_cuentan(intentos, politica)
    if politica == "ultima":
        base = [i for i in base if i["codigo"] != codigo]
    suma, creditos = _suma_y_creditos(G, base)
    return max(0.0, (objetivo * (creditos + c) - suma) / c)


def validar_notas(intentos, nota_aprobatoria):
    """Avisos si una nota contradice el estado (por ejemplo, 'aprobada' con 2.5)."""
    avisos = []
    for i in intentos:
        if i["nota"] is None:
            continue
        if i["estado"] == "aprobada" and i["nota"] < nota_aprobatoria:
            avisos.append(f"{i['codigo']} figura aprobada con {i['nota']}")
        if i["estado"] == "perdida" and i["nota"] >= nota_aprobatoria:
            avisos.append(f"{i['codigo']} figura perdida con {i['nota']}")
    return avisos


def creditos_en_promedio(G, intentos, politica="todas"):
    """Créditos que entran en el promedio."""
    return _suma_y_creditos(G, intentos_que_cuentan(intentos, politica))[1]


def estado_academico(promedio_actual, creditos, reglas):
    """Estado académico estimado (Reglamento, arts. 124 a 130).

    Distinguido: promedio >= 3.95 con 16 o más créditos. Normal: promedio >= 3.25.
    Por debajo de 3.25 el estudiante queda en riesgo de período de prueba; las consecuencias
    exactas dependen de su historia (primer ingreso, semestres cursados).
    """
    if promedio_actual is None:
        return "sin datos"
    if (promedio_actual >= reglas.get("promedio_distinguido", 3.95)
            and creditos >= reglas.get("creditos_distinguido", 16)):
        return "distinguido"
    if promedio_actual >= reglas.get("promedio_minimo", 3.25):
        return "normal"
    return "por debajo del mínimo (período de prueba)"


def simular_perdida(G, intentos, codigo, nota, reglas, politica="todas"):
    """Promedio y estado académico estimado si se pierde 'codigo' con 'nota'."""
    extra = intentos + [{"codigo": codigo, "periodo": "hipotetico", "estado": "perdida", "nota": nota}]
    nuevo = promedio(G, extra, politica)
    return nuevo, estado_academico(nuevo, creditos_en_promedio(G, extra, politica), reglas)
