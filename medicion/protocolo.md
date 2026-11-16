# Prueba piloto "antes/después": planear a mano frente a usar el programa

**Objetivo.** Comprobar si el programa reduce el tiempo y los errores al resolver tres tareas típicas de planeación
(contar créditos, ver qué se bloquea, calcular el promedio si se pierde una materia).

**Participantes.** De 4 a 8 estudiantes voluntarios, preferiblemente de Sistemas y que no sean autores del proyecto.
Anónimos (P1, P2, ...). Se les explica que es para un trabajo de clase y que pueden parar cuando quieran.

**Materiales.** Plan de estudios de Sistemas (imagen o PDF), la hoja con el historial del estudiante de validación
(`data/estudiantes/validacion_pga.csv`: materia, estado y nota), calculadora, cronómetro y el programa listo:
`python main.py --historial data/estudiantes/validacion_pga.csv` (menú).

## Procedimiento
1. Explica en un minuto de qué se trata, sin dar respuestas. Deja 30 segundos de práctica del menú (opciones 1, 4 y 5), sin cronómetro.
2. Cada participante resuelve **dos conjuntos** de tareas: uno **a mano** y otro **con el programa**. Alterna el orden y los conjuntos:

| Participante | Primero | Después |
|---|---|---|
| P1, P5 | a mano, conjunto A | programa, conjunto B |
| P2, P6 | programa, conjunto A | a mano, conjunto B |
| P3, P7 | a mano, conjunto B | programa, conjunto A |
| P4, P8 | programa, conjunto B | a mano, conjunto A |

3. **Tiempo:** empieza a contar al leer la primera tarea y detente cuando den la tercera respuesta. Anota los segundos.
4. **Correctas (0 a 3):** compara con la clave. En "materias bloqueadas" solo es correcta si la lista coincide exacta, sin faltar ni sobrar.
5. Guarda una fila por conjunto en `data/medicion/mediciones.csv` (copia la plantilla): `participante,condicion,tiempo_seg,correctas`,
   con `condicion` = `manual` o `programa`. Ejemplo: `P1,manual,540,2`.
6. Cuando termines: `python main.py --analizar-medicion data/medicion/mediciones.csv` imprime el resumen y la tabla en LaTeX para el documento.

## Tareas y claves (también con `python main.py --medicion-claves`)
**Conjunto A**
1. ¿Cuántos créditos tiene aprobados el estudiante? **Clave: 24.**
2. Si no aprueba Cálculo II, ¿qué materias se le bloquean (en cadena)? **Clave: 7** (Análisis de Datos en Ing. I, Física Electricidad,
   Examen Comprehensivo I, Soluciones Computac. a Probl. de Ing., Optimización, Cálculo III, Ecuaciones Diferenciales).
3. Si pierde Algoritmia y Programación II con 2.0, ¿cuál es su nuevo promedio? **Clave: 3.53.**

**Conjunto B**
1. ¿Cuántos créditos le faltan por aprobar, sin contar los que cursa ahora? **Clave: 118** (cursa 13).
2. Si no aprueba Algoritmia y Programación II, ¿qué materias se le bloquean (en cadena)? **Clave: 9** (Proyecto Final, POO, Estructura de Datos I y II,
   Algoritmia y Complejidad, Bases de Datos, Diseño de Software I y II, Compiladores).
3. Si pierde Cálculo II con 1.5, ¿cuál es su nuevo promedio? **Clave: 3.42.**

## Qué reportar y con qué cuidado
- Número de participantes (n), tiempo medio y exactitud en cada condición.
- Es una prueba piloto con pocas personas: describe lo que pasó, sin generalizar. El orden alternado equilibra, pero no elimina, el efecto de aprendizaje.
- Si el programa no mejora algo, dilo: también es un resultado.
