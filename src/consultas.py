"""Consultas sobre el avance de un estudiante.

Una materia está 'pendiente' si no está aprobada ni cursándose.
Prerrequisito: debe estar aprobada. Correquisito: aprobada o cursando.
"""
import math

import networkx as nx

from .grafo import subgrafo_prerreq

APROBADA = "aprobada"
CURSANDO = "cursando"


def estados_actuales(historial):
    """Estado vigente de cada materia: aprobada si alguna vez se aprobó, si no el último intento."""
    estados = {}
    for codigo, _periodo, estado in historial:
        if estados.get(codigo) == APROBADA:
            continue
        estados[codigo] = estado
    return estados


def _pendiente(estados, codigo):
    return estados.get(codigo) not in (APROBADA, CURSANDO)


def _requisitos(G, codigo, tipo):
    return [u for u, _, d in G.in_edges(codigo, data=True) if d["tipo"] == tipo]


def es_disponible(G, estados, codigo):
    prerreq = _requisitos(G, codigo, "prerreq")
    correq = _requisitos(G, codigo, "correq")
    return all(estados.get(r) == APROBADA for r in prerreq) and all(
        estados.get(r) in (APROBADA, CURSANDO) for r in correq
    )


def niveles_idioma(G):
    """Niveles de idiomas ordenados (I, II, ..., VIII)."""
    return sorted(
        (c for c in G.nodes if G.nodes[c].get("tipo") == "idioma"),
        key=lambda c: (G.nodes[c]["semestre_pensum"], c),
    )


def aplicar_nivelacion_idiomas(G, estados):
    """Si se aprobó un nivel por examen de ubicación o cursándolo, los niveles inferiores quedan cubiertos."""
    niveles = niveles_idioma(G)
    aprobados = [i for i, c in enumerate(niveles) if estados.get(c) == APROBADA]
    nuevos = dict(estados)
    if aprobados:
        for c in niveles[: max(aprobados)]:
            nuevos[c] = APROBADA
    return nuevos


def nivel_idioma(G, estados):
    """Número del nivel de idiomas más alto aprobado (0 si ninguno)."""
    niveles = niveles_idioma(G)
    aprobados = [i for i, c in enumerate(niveles) if estados.get(c) == APROBADA]
    return max(aprobados) + 1 if aprobados else 0


def siguiente_idioma(G, estados):
    """Primer nivel de idiomas que falta por aprobar (los idiomas se avanzan en orden)."""
    for c in niveles_idioma(G):
        if estados.get(c) != APROBADA:
            return c
    return None


def disponibles(G, estados):
    """Materias pendientes que el estudiante puede matricular ya.

    De idiomas solo se ofrece el siguiente nivel.
    """
    estados = aplicar_nivelacion_idiomas(G, estados)
    siguiente = siguiente_idioma(G, estados)
    return sorted(
        c
        for c in G.nodes
        if _pendiente(estados, c)
        and es_disponible(G, estados, c)
        and (G.nodes[c].get("tipo") != "idioma" or c == siguiente)
    )


def bloqueadas(G, estados):
    """Materias pendientes a las que todavía les falta algún requisito."""
    estados = aplicar_nivelacion_idiomas(G, estados)
    libres = set(disponibles(G, estados))
    return sorted(c for c in G.nodes if _pendiente(estados, c) and c not in libres)


def bloqueadas_por(G, materia, estados):
    """Materias no aprobadas que dependen (en cadena) de 'materia' por prerrequisito."""
    H = subgrafo_prerreq(G)
    return sorted(c for c in nx.descendants(H, materia) if estados.get(c) != APROBADA)


def resumen_creditos(G, estados):
    def cred(c):
        return G.nodes[c].get("creditos", 0)

    total = sum(cred(c) for c in G.nodes)
    aprobados = sum(cred(c) for c in G.nodes if estados.get(c) == APROBADA)
    en_curso = sum(cred(c) for c in G.nodes if estados.get(c) == CURSANDO)
    return {
        "total": total,
        "aprobados": aprobados,
        "en_curso": en_curso,
        "faltantes": total - aprobados - en_curso,
        "avance_pct": round(100 * aprobados / total, 1) if total else 0.0,
    }


def semestres_minimos(G, estados, reglas):
    """Cota inferior de semestres que faltan.

    Es el mayor entre: la cadena de prerrequisitos más larga entre las pendientes
    (camino más largo en el DAG) y los créditos pendientes / máximo por semestre.
    """
    pendientes = [c for c in G.nodes if _pendiente(estados, c)]
    if not pendientes:
        return {"por_cadena": 0, "por_creditos": 0, "minimo": 0}
    H = subgrafo_prerreq(G).subgraph(pendientes)
    por_cadena = nx.dag_longest_path_length(H) + 1
    cred_pend = sum(G.nodes[c].get("creditos", 0) for c in pendientes)
    por_creditos = math.ceil(cred_pend / reglas["creditos_max"])
    return {
        "por_cadena": por_cadena,
        "por_creditos": por_creditos,
        "minimo": max(por_cadena, por_creditos),
    }


GRUPOS = {
    "obligatoria": "obligatorias",
    "electiva": "electivas",
    "idioma": "idiomas",
    "examen": "otros",
    "seminario": "otros",
}


def agrupar(G, codigos):
    """Separa las materias en obligatorias, electivas, idiomas y otros requisitos (0 créditos)."""
    grupos = {"obligatorias": [], "electivas": [], "idiomas": [], "otros": []}
    orden = sorted(codigos, key=lambda c: (G.nodes[c].get("semestre_pensum", 0), c))
    for c in orden:
        grupos[GRUPOS.get(G.nodes[c].get("tipo"), "otros")].append(c)
    return grupos


def estados_si_apruebas_lo_que_cursas(estados):
    return {c: (APROBADA if e == CURSANDO else e) for c, e in estados.items()}


def disponibles_proximo_semestre(G, estados):
    """Qué podrías matricular el próximo semestre si apruebas todo lo que cursas ahora."""
    return disponibles(G, estados_si_apruebas_lo_que_cursas(estados))


def ventana_matricula(G, estados, reglas):
    """Semestres del plan que se pueden matricular a la vez (Reglamento, art. 51).

    Solo se permiten materias de 'ventana_semestres' (3) semestres consecutivos, empezando por
    el semestre más atrasado que tenga materias pendientes. Los idiomas no cuentan.
    """
    estados = aplicar_nivelacion_idiomas(G, estados)
    pendientes = [
        c for c in G.nodes if _pendiente(estados, c) and G.nodes[c].get("tipo") != "idioma"
    ]
    if not pendientes:
        return None
    inicio = min(G.nodes[c]["semestre_pensum"] for c in pendientes)
    fin = inicio + reglas.get("ventana_semestres", 3) - 1
    adelante = reglas.get("idiomas_semestres_adelante")
    if adelante is not None:  # el nivel de idiomas limita hasta qué semestre se ofrecen materias
        fin = min(fin, nivel_idioma(G, estados) + adelante)
    return inicio, fin


def disponibles_matricula(G, estados, reglas):
    """Materias disponibles por prerrequisitos que además caben en la ventana de semestres."""
    libres = disponibles(G, estados)
    ventana = ventana_matricula(G, estados, reglas)
    if ventana is None:
        return libres
    ini, fin = ventana
    return [
        c
        for c in libres
        if G.nodes[c].get("tipo") == "idioma" or ini <= G.nodes[c]["semestre_pensum"] <= fin
    ]


def matricula_proximo_semestre(G, estados, reglas):
    """Lo que podrías matricular el próximo semestre si apruebas todo lo que cursas ahora."""
    return disponibles_matricula(G, estados_si_apruebas_lo_que_cursas(estados), reglas)


def sugerir_matricula(G, estados, reglas):
    """Carga sugerida para el próximo semestre. Devuelve (códigos, créditos).

    Respeta el reglamento: primero las materias perdidas, luego las más atrasadas del plan
    (a igual semestre, las que más materias desbloquean), dentro de la ventana de semestres y
    sin pasar del máximo de créditos. Si no se llega al mínimo, se completa con electivas.
    """
    sup = estados_si_apruebas_lo_que_cursas(estados)
    libres = disponibles_matricula(G, sup, reglas)
    H = subgrafo_prerreq(G)

    def creditos(c):
        return G.nodes[c]["creditos"]

    obligatorias = [c for c in libres if G.nodes[c].get("tipo") == "obligatoria" and creditos(c) > 0]
    obligatorias.sort(
        key=lambda c: (
            sup.get(c) != "perdida",
            G.nodes[c]["semestre_pensum"],
            -len(nx.descendants(H, c)),
            c,
        )
    )
    electivas = sorted(
        (c for c in libres if G.nodes[c].get("tipo") == "electiva"),
        key=lambda c: (G.nodes[c]["semestre_pensum"], c),
    )
    elegidas, total = [], 0
    for c in obligatorias:
        if total + creditos(c) <= reglas["creditos_max"]:
            elegidas.append(c)
            total += creditos(c)
    for c in electivas:
        if total >= reglas["creditos_min"]:
            break
        if total + creditos(c) <= reglas["creditos_max"]:
            elegidas.append(c)
            total += creditos(c)
    return elegidas, total


def creditos_en_curso(G, estados):
    return sum(G.nodes[c]["creditos"] for c in G.nodes if estados.get(c) == CURSANDO)


def puede_retirar(G, estados, codigo, reglas):
    """Retiro de una materia en curso. No se permite si el estudiante queda por debajo del mínimo de créditos."""
    if estados.get(codigo) != CURSANDO:
        return False, "no se está cursando, así que no hay nada que retirar"
    restante = creditos_en_curso(G, estados) - G.nodes[codigo]["creditos"]
    minimo = reglas["creditos_min"]
    if restante < minimo:
        return False, f"no puedes retirarla: quedarías con {restante} créditos y el mínimo es {minimo}"
    return True, f"puedes retirarla: quedarías con {restante} créditos (el mínimo es {minimo})"
