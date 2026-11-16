"""Álgebra booleana aplicada a la matrícula (Unidad 2 del curso).

Cada materia x tiene dos variables booleanas:
    A_x = "x está aprobada"      C_x = "x se está cursando"
(A_x y C_x nunca son verdaderas a la vez: esa combinación es un *don't care*).

La regla "puedo matricular v" es una función booleana:

    Disponible(v) = ¬A_v · ¬C_v · R(v)
    R(v) = producto de A_u para cada prerrequisito u, por (A_w + C_w) para cada correquisito w

Aquí se construye esa función, su tabla de verdad, su forma canónica (suma de mintérminos),
su simplificación (Quine-McCluskey, que equivale a agrupar en un mapa de Karnaugh), su
negación por De Morgan, y se verifica que coincide con el código del grafo para TODOS los
estados posibles de las materias involucradas.
"""
from itertools import combinations, product

from .consultas import (APROBADA, CURSANDO, _pendiente, aplicar_nivelacion_idiomas,
                        es_disponible, siguiente_idioma, ventana_matricula)

ESTADOS = ["aprobada", "cursando", "perdida", "retirada", "sin cursar"]
GRAY = {0: [""], 1: ["0", "1"], 2: ["00", "01", "11", "10"]}


# ---------------------------------------------------------------- estructura de la regla
def _requisitos(G, v):
    prerreq = sorted(u for u, _, d in G.in_edges(v, data=True) if d["tipo"] == "prerreq")
    correq = sorted(u for u, _, d in G.in_edges(v, data=True) if d["tipo"] == "correq")
    return prerreq, correq


def variables_requisitos(G, v):
    """Variables de R(v): A_u por prerrequisito; A_w y C_w por correquisito."""
    prerreq, correq = _requisitos(G, v)
    return [f"A_{u}" for u in prerreq] + [x for w in correq for x in (f"A_{w}", f"C_{w}")]


def evaluar_requisitos(G, v, valores):
    """R(v) para una asignación {variable: 0/1}."""
    prerreq, correq = _requisitos(G, v)
    return bool(all(valores[f"A_{u}"] for u in prerreq)
                and all(valores[f"A_{w}"] or valores[f"C_{w}"] for w in correq))


def expresion_requisitos(G, v):
    prerreq, correq = _requisitos(G, v)
    factores = [f"A_{u}" for u in prerreq] + [f"(A_{w} + C_{w})" for w in correq]
    return " · ".join(factores) if factores else "1"


def negacion_requisitos(G, v):
    """¬R(v) aplicando De Morgan: ¬(a·b) = ¬a + ¬b y ¬(a+b) = ¬a·¬b."""
    prerreq, correq = _requisitos(G, v)
    terminos = [f"¬A_{u}" for u in prerreq] + [f"¬A_{w} · ¬C_{w}" for w in correq]
    return " + ".join(terminos) if terminos else "0"


def expresion_disponible(G, v):
    R = expresion_requisitos(G, v)
    return f"¬A_{v} · ¬C_{v}" + ("" if R == "1" else f" · {R}")


# ---------------------------------------------------------------- tabla de verdad
def funcion_requisitos(G, v):
    """Mintérminos (f=1) y don't cares de R(v), con la primera variable como bit más significativo."""
    variables = variables_requisitos(G, v)
    _, correq = _requisitos(G, v)
    n = len(variables)
    unos, dc = [], []
    for m in range(2 ** n):
        bits = format(m, f"0{n}b") if n else ""
        valores = {x: int(b) for x, b in zip(variables, bits)}
        if any(valores[f"A_{w}"] and valores[f"C_{w}"] for w in correq):
            dc.append(m)  # aprobada y cursando a la vez: imposible
        elif evaluar_requisitos(G, v, valores):
            unos.append(m)
    return variables, unos, dc


def tabla_verdad(G, v):
    variables, unos, dc = funcion_requisitos(G, v)
    n = len(variables)
    filas = []
    for m in range(2 ** n):
        valor = "X" if m in dc else ("1" if m in unos else "0")
        filas.append((format(m, f"0{n}b") if n else "", valor))
    return variables, filas


# ---------------------------------------------------------------- Quine-McCluskey
def _combinar(a, b):
    difieren = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    if len(difieren) == 1 and "-" not in (a[difieren[0]], b[difieren[0]]):
        i = difieren[0]
        return a[:i] + "-" + a[i + 1:]
    return None


def _primos(cadenas):
    actuales, primos = set(cadenas), set()
    while actuales:
        siguientes, usados = set(), set()
        for a in actuales:
            for b in actuales:
                c = _combinar(a, b)
                if c:
                    siguientes.add(c)
                    usados.update((a, b))
        primos |= actuales - usados
        actuales = siguientes
    return primos


def minimizar(n, unos, dont_care=()):
    """Suma de productos mínima (implicantes como cadenas de '0', '1' y '-')."""
    if not unos or n == 0:
        return []
    todos = sorted(set(unos) | set(dont_care))
    primos = sorted(_primos({format(m, f"0{n}b") for m in todos}))

    def cubre(imp, m):
        return all(i == "-" or i == b for i, b in zip(imp, format(m, f"0{n}b")))

    elegidos = []
    for m in sorted(unos):  # implicantes primos esenciales
        candidatos = [p for p in primos if cubre(p, m)]
        if len(candidatos) == 1 and candidatos[0] not in elegidos:
            elegidos.append(candidatos[0])
    por_cubrir = {m for m in unos if not any(cubre(p, m) for p in elegidos)}
    if por_cubrir:
        restantes = [p for p in primos if p not in elegidos]
        for k in range(1, len(restantes) + 1):
            hallado = next((c for c in combinations(restantes, k)
                            if all(any(cubre(p, m) for p in c) for m in por_cubrir)), None)
            if hallado:
                elegidos += list(hallado)
                break
    return sorted(elegidos)


def sop_texto(variables, implicantes):
    if not implicantes:
        return "0"
    terminos = []
    for imp in implicantes:
        literales = [(x if b == "1" else f"¬{x}") for x, b in zip(variables, imp) if b != "-"]
        terminos.append(" · ".join(literales) if literales else "1")
    return " + ".join(terminos)


def forma_canonica(unos, dc):
    texto = f"Σm({', '.join(map(str, unos))})" if unos else "0"
    return texto + (f" + d({', '.join(map(str, dc))})" if dc else "")


# ---------------------------------------------------------------- mapa de Karnaugh
def mapa_karnaugh(variables, unos, dc):
    """Mapa en texto para 1 a 4 variables (filas y columnas en código Gray); None si n > 4."""
    n = len(variables)
    if not 1 <= n <= 4:
        return None
    r = n // 2
    filas, cols = GRAY[r], GRAY[n - r]
    ancho = max(len(x) for x in variables) + 2
    cab_f, cab_c = " ".join(variables[:r]) or "-", " ".join(variables[r:])
    lineas = [f"filas: {cab_f}    columnas: {cab_c}",
              " " * 6 + "".join(c.center(ancho) for c in cols)]
    for f in filas:
        celdas = []
        for c in cols:
            m = int(f + c, 2)
            celdas.append(("X" if m in dc else "1" if m in unos else "0").center(ancho))
        lineas.append((f or "-").center(6) + "".join(celdas))
    return "\n".join(lineas)


# ---------------------------------------------------------------- verificación de equivalencia
def verificar_equivalencia(G, codigos=None):
    """Compara la expresión booleana con es_disponible() para todos los estados posibles.

    Devuelve (materias revisadas, combinaciones comprobadas, lista de fallos).
    """
    fallos, comprobadas = [], 0
    revisadas = sorted(codigos or G.nodes)
    for v in revisadas:
        prerreq, correq = _requisitos(G, v)
        involucradas = list(dict.fromkeys([v] + prerreq + correq))
        for combo in product(ESTADOS, repeat=len(involucradas)):
            estados = dict(zip(involucradas, combo))
            valores = {}
            for c, e in estados.items():
                valores[f"A_{c}"] = int(e == "aprobada")
                valores[f"C_{c}"] = int(e == "cursando")
            booleano = (not valores[f"A_{v}"]) and (not valores[f"C_{v}"]) and evaluar_requisitos(G, v, valores)
            programa = _pendiente(estados, v) and es_disponible(G, estados, v)
            comprobadas += 1
            if bool(booleano) != bool(programa):
                fallos.append((v, estados))
    return len(revisadas), comprobadas, fallos


# ---------------------------------------------------------------- respuesta Sí/No con explicación
def explicar(G, estados, v, reglas):
    """¿Puedo matricular v? Devuelve (bool, razones): cada razón es un literal falso de la regla."""
    estados = aplicar_nivelacion_idiomas(G, estados)
    nombre = lambda c: f"{G.nodes[c]['nombre']} ({c})"
    razones = []
    estado = estados.get(v)
    if estado == APROBADA:
        razones.append("ya la aprobaste (¬A es falso)")
    elif estado == CURSANDO:
        razones.append("ya la estás cursando (¬C es falso)")
    prerreq, correq = _requisitos(G, v)
    for u in prerreq:
        if estados.get(u) != APROBADA:
            razones.append(f"te falta aprobar {nombre(u)}; estado actual: {estados.get(u, 'sin cursar')}")
    for w in correq:
        if estados.get(w) not in (APROBADA, CURSANDO):
            razones.append(f"te falta aprobar o estar cursando {nombre(w)} (correquisito)")
    tipo, sem = G.nodes[v].get("tipo"), G.nodes[v]["semestre_pensum"]
    if tipo == "idioma":
        if v != siguiente_idioma(G, estados) and estado != APROBADA:
            razones.append("en idiomas solo se ofrece el siguiente nivel")
    else:
        ventana = ventana_matricula(G, estados, reglas)
        if ventana and not ventana[0] <= sem <= ventana[1]:
            razones.append(f"es del semestre {sem} del plan, fuera de la ventana de matrícula "
                           f"(semestres {ventana[0]} a {ventana[1]}, art. 51)")
    return not razones, razones


# ---------------------------------------------------------------- texto completo para la consola
def texto_booleano(G, v):
    variables, filas = tabla_verdad(G, v)
    _, unos, dc = funcion_requisitos(G, v)
    n = len(variables)
    out = [f"Álgebra booleana de {G.nodes[v]['nombre']} ({v})",
           "A_x = x aprobada;  C_x = x cursando (A_x y C_x a la vez es imposible: don't care)",
           "", f"Disponible({v}) = {expresion_disponible(G, v)}"]
    if n == 0:
        out += [f"R({v}) = 1: sin requisitos, la condición es una tautología (siempre verdadera)."]
        return "\n".join(out)
    out += [f"R({v}) = {expresion_requisitos(G, v)}",
            f"Forma canónica (suma de mintérminos): R = {forma_canonica(unos, dc)}"]
    simplificada = sop_texto(variables, minimizar(n, unos, dc))
    out += [f"Simplificada (Quine-McCluskey / Karnaugh): R = {simplificada}",
            f"Negación (De Morgan): ¬R = {negacion_requisitos(G, v)}", ""]
    if n <= 4:
        out += ["Tabla de verdad de R (X = don't care):", "  " + " ".join(variables) + "  R"]
        out += [f"  {' '.join(b.rjust(len(x)) for b, x in zip(bits, variables))}  {val}" for bits, val in filas]
    else:
        out += [f"Tabla de verdad: {2 ** n} filas; R = 1 solo en {len(unos)} de ellas (mintérminos {unos})."]
    mapa = mapa_karnaugh(variables, unos, dc)
    out += ["", "Mapa de Karnaugh:", mapa] if mapa else ["", "(El mapa de Karnaugh se dibuja hasta 4 variables.)"]
    return "\n".join(out)
