# Asistente de ruta académica

Proyecto final de **Matemáticas Discretas (MAT 4021)**, Universidad del Norte, **Grupo 7**.
Autores: Juan Ayala Díaz, Bradley De La Hoz Guerrero, Álvaro León Curvelo y Alejandro Márquez Rincón.

Orienta a un estudiante de Ingeniería de Sistemas y Computación a partir de su historial: qué materias puede matricular, qué se le
bloquea si pierde o retira una, cuántos créditos y semestres le faltan y cómo cambia su promedio.

## Teoría del curso que usa
| Unidad | Uso en el proyecto | Módulo |
|---|---|---|
| Grafos (3) | El plan de estudios es un grafo dirigido acíclico (materias, prerrequisitos y correquisitos); BFS, camino más largo | `src/grafo.py`, `src/consultas.py` |
| Álgebra booleana (2) | La regla de matrícula como función booleana: tabla de verdad, forma canónica, Quine-McCluskey (Karnaugh), De Morgan, equivalencia lógica | `src/booleano.py` |
| Análisis de redes (4) | Grado, alcance, cercanía armónica e intermediación; puntaje de importancia de cada materia | `src/importancia.py` |
| Redes neuronales (5) | Perceptrón con la regla de aprendizaje vista en clase (demostración: AND) | `src/perceptron.py` |

## Requisitos e instalación
Python 3.10 o superior. Desde la carpeta del proyecto:

**Windows (PowerShell)**
```
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```
**macOS / Linux**
```
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```
(Si ya tienes Python con las librerías, basta `python -m pip install -r requirements.txt` y `python main.py`.)

## Cómo ejecutarlo
`python main.py` abre un **menú de preguntas** (historial de ejemplo). Con el historial del caso de validación:
```
python main.py --historial data/estudiantes/validacion_pga.csv
```
Opciones de línea de comandos (se pueden combinar):
```
--todas                       materias que puedes matricular ahora
--proximo                     qué matricular el próximo semestre (y carga sugerida)
--si-retiro IST2088           qué se bloquea si no apruebas la materia (y si se puede retirar)
--si-pierdo IST2089           cuánto baja el promedio y el estado académico
--nota-necesaria IST2089 --objetivo 3.5
--puedo MAT1121               Sí/No y qué falta
--booleano MAT1111            expresión, forma canónica, De Morgan, tabla de verdad y Karnaugh
--verificar-booleano          equivalencia lógica con el grafo (62 materias, 17 750 combinaciones)
--importancia                 ranking de materias más críticas
--perceptron-and              entrenamiento del AND paso a paso
```

## Reproducir los resultados del documento
| Resultado | Comando | Esperado |
|---|---|---|
| Promedio de validación | `python main.py --historial data/estudiantes/validacion_pga.csv` | `Promedio acumulado: 3.70` |
| Equivalencia booleana | `python main.py --verificar-booleano` | coincide en las 62 materias |
| Materias críticas | `python main.py --importancia` | Estructura de Datos II, Algoritmia II, Estructura de Datos I... |
| Perceptrón (AND) | `python main.py --perceptron-and` | tres primeros pasos: b = 0.072; w₂ = −0.05; w = (−0.05, −0.05), b = −0.028 |
| Pruebas | `python -m pytest` | 72 pruebas pasan |

## Datos
- `data/sistemas/materias.csv`: 62 materias con créditos y semestre (transcritas del plan de estudios publicado por la universidad; SNIES 103821).
- `data/sistemas/prerrequisitos.csv`: 40 relaciones (39 prerrequisitos, 1 correquisito), confirmadas por un integrante.
- `data/sistemas/reglas.json`: reglas de la carrera tomadas del Reglamento de Estudiantes (carga de 7 a 17 créditos, nota 3.0, promedio mínimo 3.25, ventana de 3 semestres).
- `data/estudiantes/validacion_pga.csv`: historial anónimo de un integrante (caso con resultado conocido: PGA 3.70 en la aplicación de la universidad, que aclara que sus notas son una guía y no oficiales).
- `data/estudiantes/ejemplo.csv`: historial ilustrativo. Formato: `codigo,periodo,estado,nota` (`estado`: aprobada, perdida, retirada o cursando).
- Para otra carrera, basta agregar `data/<carrera>/` con los tres archivos y usar `--carrera <carrera>`.

## Estructura del repositorio
```
main.py            punto de entrada
src/               código fuente (carga, grafo, consultas, promedio, booleano, importancia, perceptron, cli)
tests/             72 pruebas automáticas (pytest)
data/              datos del plan, reglas e historiales
documento/         fuentes LaTeX del paper
presentacion/      fuentes Beamer de la sustentación
```

## Limitaciones
Solo Ingeniería de Sistemas y Computación. No conoce la oferta real de materias de cada semestre ni modela el límite por nivel de idiomas.
El perceptrón no se evaluó con notas reales (no se recolectaron): es una demostración del método.
La encuesta que respalda el impacto es una muestra por conveniencia (43 personas).
