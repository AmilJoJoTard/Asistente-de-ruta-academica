"""Entrada y salida por consola: menú de preguntas y opciones de línea de comandos."""
import argparse
from dataclasses import dataclass
from pathlib import Path

from . import booleano as bo
from . import consultas as q
from . import importancia as im
from . import medicion as md
from . import promedio as pr
from .carga import (cargar_dificultad, cargar_intentos, cargar_materias, cargar_prerrequisitos,
                    cargar_reglas)
from .grafo import construir_grafo, validar_pensum

RAIZ = Path(__file__).resolve().parent.parent  # carpeta del proyecto, sin importar desde dónde se ejecute

MENU = """
¿Qué quieres saber?
  1. Resumen: créditos, promedio y semestres mínimos
  2. Mostrar todas las materias que puedo matricular
  3. ¿Qué puedo matricular el próximo semestre?
  4. ¿Qué se bloquea si pierdo o retiro una materia?
  5. ¿Cuánto baja mi promedio si pierdo una materia?
  6. ¿Qué nota necesito en una materia para llegar a un promedio?
  7. ¿Puedo matricular una materia? (Sí/No y por qué)
  8. Álgebra booleana de una materia (expresión, tabla de verdad, Karnaugh)
  9. Verificar que la lógica booleana coincide con el programa
  10. ¿Qué materias son más críticas? (importancia de cada materia)
  0. Salir
"""

NOTA_OFERTA = ("Ojo: la universidad suele abrir solo parte de estas materias cada semestre. "
               "Para adelantar alguna, habla con tu coordinadora de programa.")


@dataclass
class Contexto:
    G: object
    reglas: dict
    intentos: list
    estados: dict
    politica: str
    dificultad: object = None


def _linea(G, c):
    return f"  - {c}  {G.nodes[c]['nombre']} ({G.nodes[c]['creditos']} cr)"


def _secciones(ctx, codigos, marcados=(), electivas_resumidas=False):
    G = ctx.G
    g = q.agrupar(G, codigos)
    out = []
    if g["obligatorias"]:
        out.append("Materias obligatorias:")
        out += [_linea(G, c) + (" (*)" if c in marcados else "") for c in g["obligatorias"]]
    if g["electivas"]:
        if electivas_resumidas:
            out.append(f"Electivas: {len(g['electivas'])} cupos disponibles (la lista está en la opción 2).")
        else:
            out.append(f"Electivas (cupos de créditos libres): {len(g['electivas'])} disponibles")
            out += [_linea(G, c) for c in g["electivas"]]
    if g["idiomas"]:
        titulo = "Idiomas (se pagan aparte de la matrícula), siguiente nivel:"
        if not ctx.reglas.get("idiomas_pago_aparte"):
            titulo = "Idiomas, siguiente nivel:"
        out.append(titulo)
        out += [_linea(G, c) for c in g["idiomas"]]
    if g["otros"]:
        out.append("Seminarios y exámenes (0 créditos):")
        out += [_linea(G, c) for c in g["otros"]]
    return out or ["(ninguna por ahora)"]


def _texto_ventana(ventana):
    if not ventana:
        return []
    return [f"(Reglamento art. 51: solo se matriculan materias de los semestres {ventana[0]} a "
            f"{ventana[1]} del plan)"]


def texto_resumen(ctx):
    r = q.resumen_creditos(ctx.G, ctx.estados)
    out = [f"Créditos: {r['aprobados']} aprobados, {r['en_curso']} en curso, "
           f"{r['faltantes']} faltantes de {r['total']} ({r['avance_pct']}%)"]
    actual = pr.promedio(ctx.G, ctx.intentos, ctx.politica)
    if actual is None:
        out.append("Promedio: sin notas todavía (agrega la columna 'nota' al historial)")
    else:
        estado = pr.estado_academico(actual, pr.creditos_en_promedio(ctx.G, ctx.intentos, ctx.politica), ctx.reglas)
        out.append(f"Promedio acumulado: {actual:.2f} (estado académico estimado: {estado}; "
                   f"mínimo exigido {ctx.reglas.get('promedio_minimo', 3.25)})")
    s = q.semestres_minimos(ctx.G, ctx.estados, ctx.reglas)
    out.append(f"Semestres mínimos que faltan: {s['minimo']} "
               f"(cadena: {s['por_cadena']}, créditos: {s['por_creditos']})")
    return "\n".join(out)


def texto_todas(ctx):
    ventana = q.ventana_matricula(ctx.G, ctx.estados, ctx.reglas)
    libres = q.disponibles_matricula(ctx.G, ctx.estados, ctx.reglas)
    out = ["Materias que puedes matricular ahora:"] + _texto_ventana(ventana)
    out += _secciones(ctx, libres)
    out += ["", NOTA_OFERTA]
    return "\n".join(out)


def texto_proximo(ctx):
    G = ctx.G
    supuestos = q.estados_si_apruebas_lo_que_cursas(ctx.estados)
    ahora = set(q.disponibles_matricula(G, ctx.estados, ctx.reglas))
    proximo = q.matricula_proximo_semestre(G, ctx.estados, ctx.reglas)
    nuevas = set(proximo) - ahora
    out = ["Suponiendo que apruebas todo lo que cursas ahora, el próximo semestre puedes matricular:"]
    out += _texto_ventana(q.ventana_matricula(G, supuestos, ctx.reglas))
    out += _secciones(ctx, proximo, marcados=nuevas, electivas_resumidas=True)
    if nuevas:
        out.append("(*) se desbloquea al aprobar lo que cursas ahora.")
    elegidas, total = q.sugerir_matricula(G, ctx.estados, ctx.reglas)
    out.append("")
    out.append(f"Carga sugerida: {total} créditos (carga normal: {ctx.reglas['creditos_min']} a "
               f"{ctx.reglas['creditos_max']}, art. 68):")
    out += [_linea(G, c) for c in elegidas] or ["  (ninguna)"]
    out.append("Orden de prioridad (art. 51): primero las perdidas, luego las más atrasadas del plan.")
    out += ["", NOTA_OFERTA]
    return "\n".join(out)


def texto_retiro(ctx, codigo):
    afectadas = q.bloqueadas_por(ctx.G, codigo, ctx.estados)
    out = [f"Si no apruebas {codigo}, se bloquean {len(afectadas)} materias:"]
    out += [_linea(ctx.G, c) for c in afectadas] or ["  (ninguna)"]
    orden = [c for c, _ in im.ranking(ctx.G, ctx.reglas.get("pesos_importancia"), ctx.dificultad)]
    if codigo in orden:
        out.append(f"Importancia en el plan: puesto {orden.index(codigo) + 1} de {len(orden)}.")
    _, mensaje = q.puede_retirar(ctx.G, ctx.estados, codigo, ctx.reglas)
    out += ["", f"Retiro: {mensaje}."]
    return "\n".join(out)


def texto_pierdo(ctx, codigo):
    G = ctx.G
    actual = pr.promedio(G, ctx.intentos, ctx.politica)
    minima = ctx.reglas.get("nota_minima_definitiva", 1.5)
    out = [f"Si pierdes {codigo} ({G.nodes[codigo]['creditos']} cr), tu promedio quedaría:"]
    for nota in (minima, 2.0, 2.5, 2.9):
        nuevo, estado = pr.simular_perdida(G, ctx.intentos, codigo, nota, ctx.reglas, ctx.politica)
        extra = "" if actual is None else f" ({nuevo - actual:+.2f})"
        out.append(f"  con {nota:.1f}: {nuevo:.2f}{extra} - {estado}")
    out.append(f"{minima} es la nota definitiva mínima (art. 102).")
    if actual is not None:
        out.append(f"Si la retiras (hasta la semana {ctx.reglas.get('semana_limite_retiro', 14)}), queda en "
                   f"{actual:.2f}: una materia retirada no entra al promedio (art. 58).")
    _, mensaje = q.puede_retirar(G, ctx.estados, codigo, ctx.reglas)
    out.append(f"Retiro de {codigo}: {mensaje}.")
    out.append("Si la abandonas sin retirarla, cuenta como perdida y baja el promedio (art. 62).")
    return "\n".join(out)


def texto_nota(ctx, codigo, objetivo):
    n = pr.nota_necesaria(ctx.G, ctx.intentos, codigo, objetivo, ctx.politica)
    if n is None:
        return f"{codigo} no tiene créditos y no pesa en el promedio."
    if n > 5:
        return f"No alcanzas {objetivo:.2f} con {codigo} (necesitarías {n:.2f})."
    if n == 0:
        return f"Ya alcanzas {objetivo:.2f} sin importar la nota en {codigo}."
    return f"Para llegar a {objetivo:.2f} necesitas al menos {n:.2f} en {codigo}."


def texto_puedo(ctx, codigo):
    G = ctx.G
    puede, razones = bo.explicar(G, ctx.estados, codigo, ctx.reglas)
    nombre = f"{G.nodes[codigo]['nombre']} ({codigo})"
    regla = f"Regla: Disponible({codigo}) = {bo.expresion_disponible(G, codigo)}"
    if puede:
        return f"Sí: puedes matricular {nombre}.\n{regla}"
    return "\n".join([f"No: no puedes matricular {nombre} porque:"] + [f"  - {r}" for r in razones] + [regla])


def texto_verificacion(ctx):
    materias, combinaciones, fallos = bo.verificar_equivalencia(ctx.G)
    if fallos:
        return (f"Hay {len(fallos)} diferencias entre la lógica booleana y el programa, por ejemplo en "
                f"{fallos[0][0]} con {fallos[0][1]}.")
    return (f"La expresión booleana coincide con el programa en las {materias} materias del plan, "
            f"para las {combinaciones} combinaciones de estados comprobadas (equivalencia lógica).")


def texto_importancia(ctx, top=10):
    G, pesos = ctx.G, ctx.reglas.get("pesos_importancia")
    M, puntos = im.medidas(G), im.puntaje(G, pesos, ctx.dificultad)
    orden = sorted(puntos, key=lambda v: (-puntos[v], v))[:top]
    usados = {k: w for k, w in (pesos or im.PESOS_POR_DEFECTO).items() if w > 0}
    out = [f"Materias más críticas del plan (puntaje = {', '.join(f'{w:g}·{k}' for k, w in usados.items())}, "
           f"cada componente dividido por su máximo):"]
    for i, v in enumerate(orden, 1):
        out.append(f"{i:2d}. {v}  {G.nodes[v]['nombre']}: puntaje {puntos[v]:.2f} | {G.nodes[v]['creditos']} cr | "
                   f"abre {M[v]['dependientes']} materias directas | bloquea {M[v]['descendientes']} en total | "
                   f"puente {M[v]['intermediacion']:.3f}")
    out += ["", "abre = dependientes directos (grado de salida); bloquea = todas las que dependen de ella "
                "(alcance); puente = intermediación: qué tanto pasan por ella los caminos entre otras materias."]
    return "\n".join(out)


def _pedir_codigo(ctx):
    while True:
        codigo = input("Código de la materia (Enter para volver): ").strip().upper()
        if not codigo:
            return None
        if codigo in ctx.G.nodes:
            return codigo
        print(f"  No encuentro {codigo}. Escribe un código como MAT1111.")


def menu(ctx):
    while True:
        print(MENU)
        try:
            opcion = input("Elige una opción: ").strip()
        except EOFError:
            return
        print()
        if opcion == "0":
            return
        if opcion == "1":
            print(texto_resumen(ctx))
        elif opcion == "2":
            print(texto_todas(ctx))
        elif opcion == "3":
            print(texto_proximo(ctx))
        elif opcion == "9":
            print(texto_verificacion(ctx))
        elif opcion == "10":
            print(texto_importancia(ctx))
        elif opcion in ("4", "5", "6", "7", "8"):
            codigo = _pedir_codigo(ctx)
            if codigo is None:
                continue
            if opcion == "4":
                print(texto_retiro(ctx, codigo))
            elif opcion == "7":
                print(texto_puedo(ctx, codigo))
            elif opcion == "8":
                print(bo.texto_booleano(ctx.G, codigo))
            elif opcion == "5":
                print(texto_pierdo(ctx, codigo))
            else:
                try:
                    objetivo = float(input("Promedio que quieres alcanzar (por ejemplo 3.5): ").replace(",", "."))
                except ValueError:
                    print("  Escribe un número, por ejemplo 3.5.")
                    continue
                print(texto_nota(ctx, codigo, objetivo))
        else:
            print("Opción no válida.")


def main(argv=None):
    p = argparse.ArgumentParser(description="Asistente de créditos, materias y promedio")
    p.add_argument("--carrera", default="sistemas", help="carpeta dentro de data/")
    p.add_argument("--historial", default=str(RAIZ / "data" / "estudiantes" / "validacion_pga.csv"),
                   help="CSV con el historial del estudiante (por defecto, el caso de validación)")
    p.add_argument("--datos", default=str(RAIZ / "data"), help="carpeta base de datos")
    p.add_argument("--menu", action="store_true", help="abre el menú de preguntas")
    p.add_argument("--todas", action="store_true", help="muestra todas las materias que puedes matricular")
    p.add_argument("--proximo", action="store_true", help="qué puedes matricular el próximo semestre")
    p.add_argument("--si-retiro", metavar="CODIGO", help="qué se bloquea si retiras/pierdes esta materia")
    p.add_argument("--si-pierdo", metavar="CODIGO", help="cuánto baja el promedio si pierdes esta materia")
    p.add_argument("--nota-necesaria", metavar="CODIGO", help="nota mínima en esta materia para llegar a --objetivo")
    p.add_argument("--objetivo", type=float, help="promedio que quieres alcanzar")
    p.add_argument("--puedo", metavar="CODIGO", help="¿puedo matricular esta materia? (Sí/No y por qué)")
    p.add_argument("--booleano", metavar="CODIGO", help="álgebra booleana de la materia (expresión, tabla, Karnaugh)")
    p.add_argument("--verificar-booleano", action="store_true", help="verifica la equivalencia lógica con el programa")
    p.add_argument("--importancia", action="store_true", help="ranking de materias más críticas (centralidad)")
    p.add_argument("--demo", action="store_true", help="recorrido completo con el historial de validación (sin escribir nada)")
    p.add_argument("--medicion-claves", action="store_true", help="tareas y claves de respuesta de la prueba piloto")
    p.add_argument("--analizar-medicion", metavar="ARCHIVO", help="resumen y tabla LaTeX de la prueba piloto (CSV)")
    args = p.parse_args(argv)
    if args.demo or args.medicion_claves:
        args.historial = str(RAIZ / "data" / "estudiantes" / "validacion_pga.csv")

    base = Path(args.datos) / args.carrera
    G = construir_grafo(cargar_materias(base / "materias.csv"),
                        cargar_prerrequisitos(base / "prerrequisitos.csv"))
    reglas = cargar_reglas(base / "reglas.json")
    for problema in validar_pensum(G, reglas):
        print("ADVERTENCIA:", problema)
    for codigo in (args.si_retiro, args.si_pierdo, args.nota_necesaria, args.puedo, args.booleano):
        if codigo and codigo not in G.nodes:
            p.error(f"La materia {codigo} no existe en {base / 'materias.csv'}")
    if args.nota_necesaria and args.objetivo is None:
        p.error("--nota-necesaria requiere --objetivo")

    intentos = cargar_intentos(args.historial)
    for aviso in pr.validar_notas(intentos, reglas.get("nota_aprobatoria", 3.0)):
        print("ADVERTENCIA:", aviso)
    estados = q.estados_actuales([(i["codigo"], i["periodo"], i["estado"]) for i in intentos])
    estados = q.aplicar_nivelacion_idiomas(G, estados)
    ctx = Contexto(G, reglas, intentos, estados, reglas.get("politica_repetidas", "todas"),
                   cargar_dificultad(base / "dificultad.csv"))

    preguntas = (args.todas or args.proximo or args.si_retiro or args.si_pierdo or args.nota_necesaria
                 or args.puedo or args.booleano or args.verificar_booleano or args.importancia
                 or args.demo or args.medicion_claves or args.analizar_medicion)
    if args.menu or not preguntas:
        print(f"\nAsistente de créditos y materias - {reglas['carrera']}")
        menu(ctx)
        return

    print()
    print(texto_resumen(ctx))
    if args.todas:
        print("\n" + texto_todas(ctx))
    if args.proximo:
        print("\n" + texto_proximo(ctx))
    if args.si_retiro:
        print("\n" + texto_retiro(ctx, args.si_retiro))
    if args.si_pierdo:
        print("\n" + texto_pierdo(ctx, args.si_pierdo))
    if args.nota_necesaria:
        print("\n" + texto_nota(ctx, args.nota_necesaria, args.objetivo))
    if args.puedo:
        print("\n" + texto_puedo(ctx, args.puedo))
    if args.booleano:
        print("\n" + bo.texto_booleano(ctx.G, args.booleano))
    if args.verificar_booleano:
        print("\n" + texto_verificacion(ctx))
    if args.importancia:
        print("\n" + texto_importancia(ctx))
    if args.analizar_medicion:
        print("\n" + md.texto_analisis(md.cargar_medicion(args.analizar_medicion)))
    if args.medicion_claves:
        print("\n" + md.texto_claves(ctx.G, ctx.estados, ctx.intentos, ctx.reglas, ctx.politica))
    if args.demo:
        secciones = [("1. Resumen del estudiante", texto_resumen(ctx)),
                     ("2. ¿Puedo matricular Cálculo III?", texto_puedo(ctx, "MAT1121")),
                     ("3. ¿Qué puedo matricular el próximo semestre?", texto_proximo(ctx)),
                     ("4. ¿Qué pasa si pierdo Algoritmia y Programación II?", texto_pierdo(ctx, "IST2089")),
                     ("5. Álgebra booleana de Cálculo II", bo.texto_booleano(ctx.G, "MAT1111")),
                     ("6. Materias más críticas", texto_importancia(ctx, top=5)),
                     ("7. Equivalencia lógica de la regla booleana", texto_verificacion(ctx))]
        for titulo, cuerpo in secciones:
            print("\n" + "=" * 70 + "\n" + titulo + "\n" + "=" * 70 + "\n" + cuerpo)
