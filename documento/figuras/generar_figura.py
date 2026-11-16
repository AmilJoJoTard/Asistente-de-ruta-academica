"""Genera la figura del grafo de prerrequisitos (materias obligatorias) para el documento.

Uso (desde la carpeta del proyecto):  python documento/figuras/generar_figura.py
"""
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from src.carga import cargar_materias, cargar_prerrequisitos  # noqa: E402
from src.grafo import construir_grafo  # noqa: E402

base = RAIZ / "data" / "sistemas"
G = construir_grafo(cargar_materias(base / "materias.csv"),
                    cargar_prerrequisitos(base / "prerrequisitos.csv"))

obligatorias = [c for c in G.nodes if G.nodes[c]["tipo"] == "obligatoria"]
por_semestre = defaultdict(list)
for c in sorted(obligatorias, key=lambda c: (G.nodes[c]["semestre_pensum"], c)):
    por_semestre[G.nodes[c]["semestre_pensum"]].append(c)

pos = {}
for sem, codigos in por_semestre.items():
    n = len(codigos)
    for i, c in enumerate(codigos):
        pos[c] = (sem, (n - 1) / 2 - i)

fig, ax = plt.subplots(figsize=(13, 5.6))
for u, v, d in G.edges(data=True):
    if u in pos and v in pos:
        estilo = "--" if d["tipo"] == "correq" else "-"
        ax.add_patch(FancyArrowPatch(pos[u], pos[v], arrowstyle="-|>", mutation_scale=9,
                                     linestyle=estilo, color="#555555", lw=0.9,
                                     shrinkA=15, shrinkB=15, connectionstyle="arc3,rad=0.05"))
colores = plt.cm.Blues
for c, (x, y) in pos.items():
    ax.scatter([x], [y], s=1300, color=colores(0.25 + 0.05 * G.nodes[c]["semestre_pensum"]),
               edgecolors="#1f3b5c", linewidths=0.8, zorder=3)
    ax.text(x, y, c, ha="center", va="center", fontsize=6.3, zorder=4)
for sem in por_semestre:
    ax.text(sem, 2.9, f"Sem. {sem}", ha="center", fontsize=9, fontweight="bold")
ax.set_xlim(0.4, 10.6)
ax.set_ylim(-3, 3.3)
ax.axis("off")
ax.set_title("Grafo de prerrequisitos de las materias obligatorias (línea continua: prerrequisito; "
             "discontinua: correquisito)", fontsize=9)
fig.tight_layout()
fig.savefig(Path(__file__).with_name("grafo_pensum.png"), dpi=200)
print("Figura guardada")
