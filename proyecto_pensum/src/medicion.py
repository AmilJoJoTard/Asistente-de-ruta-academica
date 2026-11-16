"""Prueba piloto "antes/después": claves de respuesta y análisis de los resultados.

Cada participante resuelve un conjunto de tres tareas A MANO (plan de estudios + calculadora) y otro
conjunto equivalente CON EL PROGRAMA, sobre el historial de validación. Se mide el tiempo y el número
de respuestas correctas (0 a 3). Las claves salen de este mismo programa.
"""
import csv
import statistics

from . import consultas as q
from . import promedio as pr


def claves(G, estados, intentos, reglas, politica="todas"):
    """Respuestas correctas de los conjuntos A y B (calculadas con el programa)."""
    resumen = q.resumen_creditos(G, estados)
    nombres = lambda codigos: ", ".join(f"{G.nodes[c]['nombre']}" for c in codigos)

    def sin_perder(codigo, nota):
        return pr.simular_perdida(G, intentos, codigo, nota, reglas, politica)[0]

    bloquea_a = q.bloqueadas_por(G, "MAT1111", estados)
    bloquea_b = q.bloqueadas_por(G, "IST2089", estados)
    return {
        "A": [f"{resumen['aprobados']} créditos aprobados",
              f"{len(bloquea_a)} materias se bloquean: {nombres(bloquea_a)}",
              f"promedio {sin_perder('IST2089', 2.0):.2f}"],
        "B": [f"{resumen['faltantes']} créditos faltantes (sin contar los {resumen['en_curso']} que cursa)",
              f"{len(bloquea_b)} materias se bloquean: {nombres(bloquea_b)}",
              f"promedio {sin_perder('MAT1111', 1.5):.2f}"],
    }


def texto_claves(G, estados, intentos, reglas, politica="todas"):
    k = claves(G, estados, intentos, reglas, politica)
    tareas = {
        "A": ["¿Cuántos créditos tiene aprobados el estudiante?",
              "Si no aprueba Cálculo II, ¿qué materias se le bloquean (en cadena)?",
              "Si pierde Algoritmia y Programación II con 2.0, ¿cuál es su nuevo promedio?"],
        "B": ["¿Cuántos créditos le faltan por aprobar, sin contar los que cursa ahora?",
              "Si no aprueba Algoritmia y Programación II, ¿qué materias se le bloquean (en cadena)?",
              "Si pierde Cálculo II con 1.5, ¿cuál es su nuevo promedio?"],
    }
    out = []
    for c in ("A", "B"):
        out.append(f"Conjunto {c}:")
        out += [f"  {i}. {t}\n     Clave: {r}" for i, (t, r) in enumerate(zip(tareas[c], k[c]), 1)]
    return "\n".join(out)


def cargar_medicion(ruta):
    with open(ruta, newline="", encoding="utf-8") as f:
        return [{"participante": r["participante"].strip(), "condicion": r["condicion"].strip().lower(),
                 "tiempo_seg": float(r["tiempo_seg"]), "correctas": int(r["correctas"])}
                for r in csv.DictReader(f)]


def analizar(filas):
    """Resumen por condición ('manual' o 'programa')."""
    resumen = {}
    for cond in ("manual", "programa"):
        sel = [r for r in filas if r["condicion"] == cond]
        if sel:
            resumen[cond] = {"n": len(sel),
                             "tiempo_medio": statistics.mean(r["tiempo_seg"] for r in sel),
                             "tiempo_mediana": statistics.median(r["tiempo_seg"] for r in sel),
                             "aciertos_medios": statistics.mean(r["correctas"] for r in sel),
                             "exactitud": sum(r["correctas"] for r in sel) / (3 * len(sel))}
    return resumen


def texto_analisis(filas):
    r = analizar(filas)
    if "manual" not in r or "programa" not in r:
        return "Faltan filas de una de las dos condiciones (manual y programa)."
    m, p = r["manual"], r["programa"]
    reduccion = 100 * (1 - p["tiempo_medio"] / m["tiempo_medio"])
    out = [f"Participantes: {m['n']} a mano y {p['n']} con el programa.",
           f"Tiempo medio: {m['tiempo_medio'] / 60:.1f} min a mano; {p['tiempo_medio'] / 60:.1f} min con el programa "
           f"({reduccion:.0f} % menos).",
           f"Exactitud: {m['exactitud']:.0%} a mano; {p['exactitud']:.0%} con el programa.",
           "",
           "Tabla para el documento (LaTeX):",
           r"\begin{table}[htbp]\centering",
           r"\caption{Prueba piloto: planear a mano frente a usar el programa}\label{tab:medicion}",
           r"\begin{tabular}{lrrr}\toprule",
           r"Condición & Personas & Tiempo medio (min) & Exactitud \\ \midrule",
           f"A mano & {m['n']} & {m['tiempo_medio'] / 60:.1f} & {m['exactitud']:.0%} ".replace("%", r"\%") + r"\\",
           f"Con el programa & {p['n']} & {p['tiempo_medio'] / 60:.1f} & {p['exactitud']:.0%} ".replace("%", r"\%") + r"\\",
           r"\bottomrule\end{tabular}\end{table}"]
    return "\n".join(out)
