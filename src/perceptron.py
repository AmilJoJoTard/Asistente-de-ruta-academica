"""Perceptrón (Unidad 5), con el algoritmo visto en clase.

    z = x1·w1 + ... + xn·wn + b          ŷ = φ(z)  (escalón: 1 si z >= 0, 0 si z < 0)
    error = y_real - ŷ                   w_i <- w_i + γ·error·x_i        b <- b + γ·error
con tasa de aprendizaje γ = 0.05, pesos iniciales 0 y sesgo inicial b = 0.122 (como en el ejemplo
del AND de los apuntes). Se aplica a una clasificación binaria: ¿aprobará la materia (nota >= 3.0)?
"""
import csv
import random

APRUEBA = 3.0


def escalon(z):
    return 1 if z >= 0 else 0


class Perceptron:
    def __init__(self, n_entradas, sesgo=0.122, tasa=0.05):
        self.pesos = [0.0] * n_entradas
        self.sesgo = sesgo
        self.tasa = tasa

    def z(self, x):
        return sum(xi * wi for xi, wi in zip(x, self.pesos)) + self.sesgo

    def predecir(self, x):
        return escalon(self.z(x))

    def paso(self, x, y):
        """Un paso de entrenamiento con un ejemplo. Devuelve (z, y_pred, error)."""
        z = self.z(x)
        y_pred = escalon(z)
        error = y - y_pred
        self.pesos = [w + self.tasa * error * xi for w, xi in zip(self.pesos, x)]
        self.sesgo += self.tasa * error
        return z, y_pred, error

    def entrenar(self, datos, epocas=1000):
        """Recorre los datos hasta que una época no tenga errores. Devuelve (épocas, errores de la última)."""
        errores = 0
        for e in range(1, epocas + 1):
            errores = sum(self.paso(x, y)[2] != 0 for x, y in datos)
            if errores == 0:
                return e, 0
        return epocas, errores

    def exactitud(self, datos):
        return sum(self.predecir(x) == y for x, y in datos) / len(datos) if datos else 0.0


AND = [((0, 0), 0), ((0, 1), 0), ((1, 0), 0), ((1, 1), 1)]


def traza_and():
    """Entrenamiento del AND paso a paso, igual que en los apuntes. Devuelve (líneas, perceptrón)."""
    p = Perceptron(2)
    lineas = [f"Perceptrón para AND: w = (0, 0), b = {p.sesgo}, tasa de aprendizaje = {p.tasa}"]
    for i, (x, y) in enumerate(AND, 1):
        z, y_pred, error = p.paso(x, y)
        lineas.append(f"Paso {i}: x = {x}, y = {y} | z = {z:.3f}, ŷ = {y_pred}, error = {error:+d} "
                      f"-> w = ({p.pesos[0]:.3f}, {p.pesos[1]:.3f}), b = {p.sesgo:.3f}")
    epocas, errores = p.entrenar(AND)
    lineas.append(f"Siguiendo el mismo procedimiento converge en {epocas} épocas más: "
                  f"w = ({p.pesos[0]:.3f}, {p.pesos[1]:.3f}), b = {p.sesgo:.3f}")
    lineas.append("Comprobación: " + ", ".join(f"AND{x} = {p.predecir(x)}" for x, _ in AND))
    return lineas, p


# ---------------------------------------------------------------- aplicación: ¿aprobaré?
def generar_datos_simulados(n=60, semilla=7):
    """DATOS SIMULADOS, solo para probar el método cuando no hay datos reales.

    Supuesto (inventado): nota_destino = 0.55·nota_origen + 1.3 + ruido normal(0, 0.45), entre 1.5 y 5.
    Con datos simulados el modelo solo recupera el supuesto: no es evidencia sobre estudiantes reales.
    """
    rng = random.Random(semilla)
    filas = []
    for _ in range(n):
        origen = round(rng.uniform(1.5, 5.0), 1)
        destino = round(min(5.0, max(1.5, 0.55 * origen + 1.3 + rng.gauss(0, 0.45))), 1)
        filas.append({"nota_origen": origen, "nota_destino": destino})
    return filas


def cargar_pares(ruta, columnas_x=("nota_origen",), columna_y="nota_destino"):
    with open(ruta, newline="", encoding="utf-8") as f:
        return filas_a_datos(list(csv.DictReader(f)), columnas_x, columna_y)


def filas_a_datos(filas, columnas_x=("nota_origen",), columna_y="nota_destino"):
    """Convierte filas de notas a ((x1/5, ..., xn/5), y) con y = 1 si nota_destino >= 3.0."""
    datos = []
    for f in filas:
        x = tuple(float(str(f[c]).replace(",", ".")) / 5 for c in columnas_x)
        y = 1 if float(str(f[columna_y]).replace(",", ".")) >= APRUEBA else 0
        datos.append((x, y))
    return datos


def dividir(datos, proporcion=0.7, semilla=1):
    copia = list(datos)
    random.Random(semilla).shuffle(copia)
    corte = int(len(copia) * proporcion)
    return copia[:corte], copia[corte:]


def evaluar(datos, epocas=1000, semilla=1):
    """Entrena con el 70 % y evalúa con el 30 %. Compara contra el modelo trivial (clase mayoritaria)."""
    train, test = dividir(datos, semilla=semilla)
    p = Perceptron(len(datos[0][0]))
    p.entrenar(train, epocas)
    mayoritaria = round(sum(y for _, y in train) / len(train))
    base = sum(y == mayoritaria for _, y in test) / len(test) if test else 0.0
    return {"modelo": p, "n_train": len(train), "n_test": len(test),
            "exactitud_train": p.exactitud(train), "exactitud_test": p.exactitud(test),
            "exactitud_base": base}


def umbral_nota(modelo):
    """Nota de origen a partir de la cual el modelo predice 'aprueba' (solo con una entrada)."""
    if len(modelo.pesos) != 1 or modelo.pesos[0] <= 0:
        return None
    return -modelo.sesgo / modelo.pesos[0] * 5
