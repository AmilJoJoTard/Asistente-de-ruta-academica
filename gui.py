"""Punto de entrada de la interfaz gráfica: python gui.py"""
import argparse

from src.gui import main

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Asistente de ruta académica (interfaz gráfica)")
    p.add_argument("--carrera", default="sistemas")
    p.add_argument("--historial", default=None, help="CSV con el historial del estudiante")
    a = p.parse_args()
    main(a.carrera, a.historial)
