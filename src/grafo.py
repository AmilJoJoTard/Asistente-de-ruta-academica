"""Construcción y validación del grafo de prerrequisitos."""
import networkx as nx


def construir_grafo(materias, prerrequisitos):
    """Grafo dirigido: arista requisito -> materia, con atributo 'tipo'."""
    G = nx.DiGraph()
    for codigo, datos in materias.items():
        G.add_node(codigo, **datos)
    for materia, requisito, tipo in prerrequisitos:
        G.add_edge(requisito, materia, tipo=tipo)
    return G


def subgrafo_prerreq(G):
    """Solo las aristas de prerrequisito (los correquisitos no bloquean en cadena)."""
    H = nx.DiGraph()
    H.add_nodes_from(G.nodes(data=True))
    H.add_edges_from((u, v) for u, v, d in G.edges(data=True) if d["tipo"] == "prerreq")
    return H


def validar_pensum(G, reglas=None):
    """Devuelve una lista de problemas encontrados (vacía si todo está bien)."""
    problemas = []
    for codigo in G.nodes:
        if "creditos" not in G.nodes[codigo]:
            problemas.append(f"{codigo} aparece como requisito pero no está en materias.csv")
    H = subgrafo_prerreq(G)
    if not nx.is_directed_acyclic_graph(H):
        ciclo = nx.find_cycle(H)
        problemas.append("Ciclo de prerrequisitos: " + " -> ".join(u for u, _ in ciclo))
    if reglas is not None:
        total = sum(d.get("creditos", 0) for _, d in G.nodes(data=True))
        if total != reglas["creditos_total"]:
            problemas.append(
                f"Los créditos suman {total}, pero reglas.json dice {reglas['creditos_total']}"
            )
    return problemas
