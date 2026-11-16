"""Lectura de los archivos de datos (CSV y JSON)."""
import csv
import json
from pathlib import Path

ESTADOS_VALIDOS = {"aprobada", "perdida", "retirada", "cursando"}
TIPOS_ARISTA = {"prerreq", "correq"}


def _leer_csv(ruta):
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def cargar_materias(ruta):
    """Devuelve {codigo: {nombre, creditos, semestre_pensum, tipo}}."""
    materias = {}
    for fila in _leer_csv(ruta):
        materias[fila["codigo"].strip()] = {
            "nombre": fila["nombre"].strip(),
            "creditos": int(fila["creditos"]),
            "semestre_pensum": int(fila["semestre_pensum"]),
            "tipo": fila["tipo"].strip(),
        }
    return materias


def cargar_prerrequisitos(ruta):
    """Devuelve una lista de tuplas (materia, requisito, tipo)."""
    aristas = []
    for fila in _leer_csv(ruta):
        tipo = fila["tipo"].strip()
        if tipo not in TIPOS_ARISTA:
            raise ValueError(f"Tipo de requisito inválido: {tipo!r}")
        aristas.append((fila["materia"].strip(), fila["requisito"].strip(), tipo))
    return aristas


def cargar_reglas(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def cargar_intentos(ruta):
    """Lee el historial. Cada fila es un intento: {codigo, periodo, estado, nota}.

    La columna 'nota' es opcional (escala 0 a 5, coma o punto decimal). Si falta, nota = None.
    """
    intentos = []
    for fila in _leer_csv(ruta):
        estado = fila["estado"].strip()
        if estado not in ESTADOS_VALIDOS:
            raise ValueError(f"Estado inválido: {estado!r}")
        texto = (fila.get("nota") or "").strip()
        nota = float(texto.replace(",", ".")) if texto else None
        if nota is not None and not 0 <= nota <= 5:
            raise ValueError(f"Nota fuera de la escala 0 a 5: {nota}")
        intentos.append(
            {
                "codigo": fila["codigo"].strip(),
                "periodo": fila["periodo"].strip(),
                "estado": estado,
                "nota": nota,
            }
        )
    return intentos


def cargar_historial(ruta):
    """Devuelve una lista de tuplas (codigo, periodo, estado), en orden cronológico."""
    return [(i["codigo"], i["periodo"], i["estado"]) for i in cargar_intentos(ruta)]


def cargar_dificultad(ruta):
    """Dificultad percibida (1 a 5) por materia, de la encuesta. Devuelve None si no hay archivo."""
    if not Path(ruta).exists():
        return None
    return {f["codigo"].strip(): float(f["dificultad"].replace(",", ".")) for f in _leer_csv(ruta)}
