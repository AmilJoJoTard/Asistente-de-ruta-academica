"""Importancia de cada materia dentro del plan (Unidad 4: medidas de centralidad).

Se mide sobre la red de prerrequisitos (dirigida: u -> v si u es prerrequisito de v):
  - dependientes:  grado de salida, cuántas materias se abren directamente al aprobarla.
  - descendientes: cuántas materias dependen de ella, directa o indirectamente (alcance).
  - cercanía armónica: variante para redes NO conexas (la del plan tiene varias componentes).
  - intermediación: cuántos de los caminos más cortos entre otras materias pasan por ella (puente).
Sobre esas medidas se construye un puntaje de importancia ponderado (créditos, bloqueo, puente
y, si hay datos de la encuesta, dificultad percibida). Los pesos son una decisión de modelación.
"""
import networkx as nx

from .grafo import subgrafo_prerreq

PESOS_POR_DEFECTO = {"creditos": 0.2, "bloqueo": 0.5, "puente": 0.3, "dificultad": 0.0}


def red_de_prerrequisitos(G):
    """Subgrafo de prerrequisitos sin las materias aisladas (electivas, idiomas, seminarios)."""
    H = subgrafo_prerreq(G)
    H.remove_nodes_from([n for n in list(H) if H.degree(n) == 0])
    return H


def medidas(G):
    H = red_de_prerrequisitos(G)
    n = H.number_of_nodes()
    puente = nx.betweenness_centrality(H, normalized=True)
    resultado = {}
    for v in H:
        distancias = nx.single_source_shortest_path_length(H, v)
        resultado[v] = {
            "dependientes": H.out_degree(v),
            "grado": H.out_degree(v) / (n - 1),
            "descendientes": len(distancias) - 1,
            "cercania_armonica": sum(1 / d for u, d in distancias.items() if u != v) / (n - 1),
            "intermediacion": puente[v],
        }
    return resultado


def puntaje(G, pesos=None, dificultad=None):
    """Puntaje de importancia en [0, 1] por materia: suma ponderada de componentes normalizadas."""
    M = medidas(G)
    pesos = dict(PESOS_POR_DEFECTO if pesos is None else pesos)
    componentes = {
        "creditos": {v: G.nodes[v]["creditos"] for v in M},
        "bloqueo": {v: M[v]["descendientes"] for v in M},
        "puente": {v: M[v]["intermediacion"] for v in M},
    }
    if dificultad and pesos.get("dificultad", 0) > 0:
        componentes["dificultad"] = {v: dificultad.get(v, 0.0) for v in M}
    pesos = {k: pesos.get(k, 0.0) for k in componentes}
    total = sum(pesos.values()) or 1.0
    normalizados = {}
    for k, valores in componentes.items():
        maximo = max(valores.values()) or 1.0
        normalizados[k] = {v: x / maximo for v, x in valores.items()}
    return {v: sum(pesos[k] * normalizados[k][v] for k in componentes) / total for v in M}


def ranking(G, pesos=None, dificultad=None):
    """Lista de (código, puntaje) de la más a la menos importante."""
    p = puntaje(G, pesos, dificultad)
    return sorted(p.items(), key=lambda t: (-t[1], t[0]))
