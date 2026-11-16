"""Revisión previa a la entrega: marcadores sin completar y archivos esenciales.

Uso:  python verificar_entrega.py
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
problemas = []

for ruta in (RAIZ / "documento" / "main.tex", RAIZ / "presentacion" / "presentacion.tex"):
    if not ruta.exists():
        problemas.append(f"Falta {ruta.relative_to(RAIZ)}")
        continue
    for n, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
        if linea.lstrip().startswith("%") or "newcommand{\\pendiente}" in linea:
            continue
        if "USUARIO/REPOSITORIO" in linea:
            problemas.append(f"{ruta.name}:{n}: falta el enlace real del repositorio")
        if "\\pendiente{" in linea:
            problemas.append(f"{ruta.name}:{n}: hay un texto pendiente en rojo")

for esencial in ("README.md", "requirements.txt", "main.py", "src", "tests", "data/sistemas/materias.csv"):
    if not (RAIZ / esencial).exists():
        problemas.append(f"Falta {esencial}")

if problemas:
    print("Pendientes antes de entregar:")
    print("\n".join(f"  - {p}" for p in problemas))
    sys.exit(1)
print("Todo listo: sin pendientes en los .tex y con los archivos esenciales.")
