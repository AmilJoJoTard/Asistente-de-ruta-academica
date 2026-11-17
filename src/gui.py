"""Interfaz gráfica (tkinter) del asistente de ruta académica.

Reutiliza la misma lógica que la consola: todas las respuestas salen de las funciones
`texto_*` de `src/cli.py`, así que la GUI y la terminal siempre dan el mismo resultado.
"""
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import booleano as bo
from . import consultas as q
from . import promedio as pr
from .carga import (cargar_dificultad, cargar_intentos, cargar_materias, cargar_prerrequisitos,
                    cargar_reglas)
from .cli import (RAIZ, Contexto, texto_importancia, texto_nota, texto_pierdo, texto_proximo,
                  texto_puedo, texto_resumen, texto_retiro, texto_todas, texto_verificacion)
from .grafo import construir_grafo, validar_pensum

# Paleta
BG = "#f4f6fa"
PANEL = "#ffffff"
SIDEBAR = "#1f2a44"
SIDEBAR_HOVER = "#2d3b61"
ACENTO = "#2f6fed"
TEXTO = "#1c2333"
SUAVE = "#6b7491"
OK = "#1e9e5a"
ALERTA = "#d98a00"
MAL = "#d6453d"

FUENTE = ("Segoe UI", 10)
MONO = ("Consolas", 10)

# (clave, texto del botón, necesita materia, necesita objetivo)
PREGUNTAS = [
    ("resumen", "Resumen", False, False),
    ("todas", "Qué puedo matricular ahora", False, False),
    ("proximo", "Próximo semestre", False, False),
    ("puedo", "¿Puedo matricular…?", True, False),
    ("retiro", "Si pierdo o retiro…", True, False),
    ("pierdo", "Impacto en mi promedio", True, False),
    ("nota", "Nota que necesito", True, True),
    ("importancia", "Materias críticas", False, False),
    ("booleano", "Álgebra booleana", True, False),
    ("verificar", "Verificar lógica", False, False),
    ("historial", "Mi historial", False, False),
]

AYUDA = {
    "resumen": "Créditos, promedio y semestres mínimos que te faltan.",
    "todas": "Todas las materias cuyos requisitos ya cumples.",
    "proximo": "Qué podrás matricular si apruebas lo que cursas ahora.",
    "puedo": "Elige una materia y te digo si puedes matricularla y por qué.",
    "retiro": "Elige una materia: qué se bloquea si no la apruebas y si puedes retirarla.",
    "pierdo": "Elige una materia: cuánto baja tu promedio si la pierdes.",
    "nota": "Elige una materia y el promedio al que quieres llegar.",
    "importancia": "Ranking de materias que más pesan en el plan de estudios.",
    "booleano": "Expresión, forma canónica, tabla de verdad y Karnaugh de la materia.",
    "verificar": "Comprueba que la regla booleana coincide con el programa (puede tardar unos segundos).",
    "historial": "Materias y notas cargadas desde el CSV.",
}


class App(tk.Tk):
    def __init__(self, carrera="sistemas", historial=None, datos=None):
        super().__init__()
        self.title("Asistente de ruta académica")
        self.geometry("1180x760")
        self.minsize(980, 620)
        self.configure(bg=BG)

        self.carrera = carrera
        self.datos = Path(datos) if datos else RAIZ / "data"
        self.historial = Path(historial) if historial else RAIZ / "data" / "estudiantes" / "validacion_pga.csv"
        self.ctx = None
        self.pregunta = tk.StringVar(value="resumen")
        self.materia_var = tk.StringVar()
        self.objetivo_var = tk.StringVar(value="3.5")
        self._todas_las_materias = []
        self._botones = {}

        self._estilos()
        self._construir()
        self.cargar(self.historial)
        self.seleccionar("resumen")

    # ------------------------------------------------------------------ estilos
    def _estilos(self):
        s = ttk.Style(self)
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        s.configure(".", font=FUENTE, background=BG, foreground=TEXTO)
        s.configure("TFrame", background=BG)
        s.configure("Card.TFrame", background=PANEL)
        s.configure("TLabel", background=BG, foreground=TEXTO)
        s.configure("Card.TLabel", background=PANEL)
        s.configure("Suave.TLabel", background=BG, foreground=SUAVE)
        s.configure("Valor.TLabel", background=PANEL, font=("Segoe UI", 20, "bold"))
        s.configure("Titulo.TLabel", background=BG, font=("Segoe UI", 16, "bold"))
        s.configure("Acento.TButton", background=ACENTO, foreground="white", padding=(14, 6), borderwidth=0)
        s.map("Acento.TButton", background=[("active", "#2559c4"), ("disabled", "#a9b8de")])
        s.configure("Sec.TButton", background="#e3e8f3", foreground=TEXTO, padding=(12, 6), borderwidth=0)
        s.map("Sec.TButton", background=[("active", "#d3dbec")])
        s.configure("Horizontal.TProgressbar", troughcolor="#e3e8f3", background=ACENTO, thickness=8)
        s.configure("Treeview", rowheight=26, background=PANEL, fieldbackground=PANEL, borderwidth=0)
        s.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#e3e8f3")

    # --------------------------------------------------------------- construcción
    def _construir(self):
        # barra lateral
        lateral = tk.Frame(self, bg=SIDEBAR, width=250)
        lateral.pack(side="left", fill="y")
        lateral.pack_propagate(False)
        tk.Label(lateral, text="Ruta\nacadémica", bg=SIDEBAR, fg="white", justify="left",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=20, pady=(22, 2))
        self.lbl_carrera = tk.Label(lateral, text="", bg=SIDEBAR, fg="#aab6d6", justify="left",
                                    wraplength=210, font=("Segoe UI", 9))
        self.lbl_carrera.pack(anchor="w", padx=20, pady=(0, 18))
        for clave, texto, _, _ in PREGUNTAS:
            b = tk.Label(lateral, text=texto, bg=SIDEBAR, fg="white", anchor="w", padx=20, pady=9,
                         font=("Segoe UI", 10), cursor="hand2")
            b.pack(fill="x")
            b.bind("<Button-1>", lambda _e, c=clave: self.seleccionar(c))
            b.bind("<Enter>", lambda _e, w=b, c=clave: w.configure(bg=SIDEBAR_HOVER))
            b.bind("<Leave>", lambda _e, w=b, c=clave: self._resaltar(w, c))
            self._botones[clave] = b

        # zona principal
        principal = ttk.Frame(self, padding=(22, 18))
        principal.pack(side="left", fill="both", expand=True)

        cab = ttk.Frame(principal)
        cab.pack(fill="x")
        self.lbl_titulo = ttk.Label(cab, text="", style="Titulo.TLabel")
        self.lbl_titulo.pack(side="left")
        self.lbl_archivo = ttk.Label(cab, text="", style="Suave.TLabel")
        self.lbl_archivo.pack(side="right", padx=12)

        # tarjetas de métricas
        tarjetas = ttk.Frame(principal)
        tarjetas.pack(fill="x", pady=(14, 12))
        self.val = {}
        for i, (clave, titulo) in enumerate([("creditos", "Créditos aprobados"), ("promedio", "Promedio acumulado"),
                                              ("estado", "Estado académico"), ("semestres", "Semestres mínimos")]):
            tarjetas.columnconfigure(i, weight=1, uniform="t")
            card = ttk.Frame(tarjetas, style="Card.TFrame", padding=(14, 10))
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            ttk.Label(card, text=titulo, style="Card.TLabel", foreground=SUAVE).pack(anchor="w")
            lbl = ttk.Label(card, text="–", style="Valor.TLabel")
            lbl.pack(anchor="w")
            self.val[clave] = lbl
            if clave == "creditos":
                self.barra = ttk.Progressbar(card, maximum=100)
                self.barra.pack(fill="x", pady=(4, 0))

        # barra de consulta
        consulta = ttk.Frame(principal, style="Card.TFrame", padding=(14, 10))
        consulta.pack(fill="x")
        self.lbl_ayuda = ttk.Label(consulta, text="", style="Card.TLabel", foreground=SUAVE)
        self.lbl_ayuda.grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 8))
        self.lbl_materia = ttk.Label(consulta, text="Materia", style="Card.TLabel")
        self.lbl_materia.grid(row=1, column=0, sticky="w")
        self.combo = ttk.Combobox(consulta, textvariable=self.materia_var, width=52)
        self.combo.grid(row=1, column=1, padx=8, sticky="we")
        self.combo.bind("<KeyRelease>", self._filtrar)
        self.combo.bind("<Return>", lambda _e: self.consultar())
        self.lbl_objetivo = ttk.Label(consulta, text="Promedio objetivo", style="Card.TLabel")
        self.lbl_objetivo.grid(row=1, column=2, padx=(12, 0))
        self.ent_objetivo = ttk.Entry(consulta, textvariable=self.objetivo_var, width=6)
        self.ent_objetivo.grid(row=1, column=3, padx=8)
        self.ent_objetivo.bind("<Return>", lambda _e: self.consultar())
        self.btn = ttk.Button(consulta, text="Consultar", style="Acento.TButton", command=self.consultar)
        self.btn.grid(row=1, column=4, padx=(8, 0))
        consulta.columnconfigure(1, weight=1)

        # resultado
        self.marco = ttk.Frame(principal, style="Card.TFrame", padding=2)
        self.marco.pack(fill="both", expand=True, pady=(12, 0))
        self.texto = tk.Text(self.marco, wrap="word", font=MONO, bg=PANEL, fg=TEXTO, relief="flat",
                             padx=14, pady=12, state="disabled", spacing1=2)
        sb = ttk.Scrollbar(self.marco, command=self.texto.yview)
        self.texto.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.texto.pack(side="left", fill="both", expand=True)
        self.texto.tag_configure("titulo", font=("Consolas", 11, "bold"), foreground=ACENTO)
        self.texto.tag_configure("si", foreground=OK, font=("Consolas", 12, "bold"))
        self.texto.tag_configure("no", foreground=MAL, font=("Consolas", 12, "bold"))
        self.texto.tag_configure("aviso", foreground=ALERTA)

        # tabla del historial
        cols = ("codigo", "materia", "periodo", "estado", "nota")
        self.tabla = ttk.Treeview(self.marco, columns=cols, show="headings")
        for c, t, w in [("codigo", "Código", 90), ("materia", "Materia", 340), ("periodo", "Periodo", 80),
                        ("estado", "Estado", 100), ("nota", "Nota", 70)]:
            self.tabla.heading(c, text=t)
            self.tabla.column(c, width=w, anchor="w")
        self.tabla.tag_configure("aprobada", foreground=OK)
        self.tabla.tag_configure("perdida", foreground=MAL)
        self.tabla.tag_configure("retirada", foreground=ALERTA)
        self.tabla.tag_configure("cursando", foreground=ACENTO)

        self.estado_bar = ttk.Label(principal, text="", style="Suave.TLabel")
        self.estado_bar.pack(anchor="w", pady=(6, 0))

    # ------------------------------------------------------------------- datos
    def cargar(self, ruta):
        try:
            base = self.datos / self.carrera
            G = construir_grafo(cargar_materias(base / "materias.csv"),
                                cargar_prerrequisitos(base / "prerrequisitos.csv"))
            reglas = cargar_reglas(base / "reglas.json")
            intentos = cargar_intentos(ruta)
            avisos = list(validar_pensum(G, reglas))
            avisos += pr.validar_notas(intentos, reglas.get("nota_aprobatoria", 3.0))
            estados = q.estados_actuales([(i["codigo"], i["periodo"], i["estado"]) for i in intentos])
            estados = q.aplicar_nivelacion_idiomas(G, estados)
            self.ctx = Contexto(G, reglas, intentos, estados, reglas.get("politica_repetidas", "todas"),
                                cargar_dificultad(base / "dificultad.csv"))
        except Exception as e:  # archivo mal formado, ruta inexistente, etc.
            messagebox.showerror("No pude cargar los datos", f"{type(e).__name__}: {e}")
            return False
        self.historial = Path(ruta)
        self.lbl_carrera.configure(text=reglas["carrera"])
        self.lbl_archivo.configure(text=self.historial.name)
        self._todas_las_materias = [f"{c} — {G.nodes[c]['nombre']}" for c in sorted(G.nodes)]
        self.combo.configure(values=self._todas_las_materias)
        self.estado_bar.configure(text=("⚠ " + " | ".join(avisos)) if avisos else "")
        self._actualizar_tarjetas()
        self._llenar_tabla()
        if self.pregunta.get():
            self.consultar()
        return True

    def elegir_historial(self):
        ruta = filedialog.askopenfilename(
            title="Elige tu historial (CSV: codigo,periodo,estado,nota)",
            initialdir=str(RAIZ / "data" / "estudiantes"), filetypes=[("CSV", "*.csv"), ("Todos", "*.*")])
        if ruta:
            self.cargar(ruta)

    def _actualizar_tarjetas(self):
        ctx = self.ctx
        r = q.resumen_creditos(ctx.G, ctx.estados)
        self.val["creditos"].configure(text=f"{r['aprobados']} / {r['total']}")
        self.barra.configure(value=r["avance_pct"])
        actual = pr.promedio(ctx.G, ctx.intentos, ctx.politica)
        if actual is None:
            self.val["promedio"].configure(text="–", foreground=SUAVE)
            self.val["estado"].configure(text="–", foreground=SUAVE)
        else:
            estado = pr.estado_academico(actual, pr.creditos_en_promedio(ctx.G, ctx.intentos, ctx.politica),
                                         ctx.reglas)
            minimo = ctx.reglas.get("promedio_minimo", 3.25)
            self.val["promedio"].configure(text=f"{actual:.2f}", foreground=OK if actual >= minimo else MAL)
            self.val["estado"].configure(text=str(estado), foreground=TEXTO)
        s = q.semestres_minimos(ctx.G, ctx.estados, ctx.reglas)
        self.val["semestres"].configure(text=str(s["minimo"]))

    def _llenar_tabla(self):
        self.tabla.delete(*self.tabla.get_children())
        G = self.ctx.G
        for i in self.ctx.intentos:
            nombre = G.nodes[i["codigo"]]["nombre"] if i["codigo"] in G.nodes else "(no está en el plan)"
            nota = "" if i["nota"] is None else f"{i['nota']:.1f}"
            self.tabla.insert("", "end", values=(i["codigo"], nombre, i["periodo"], i["estado"], nota),
                              tags=(i["estado"],))

    # ------------------------------------------------------------ interacción
    def _resaltar(self, widget, clave):
        widget.configure(bg=ACENTO if clave == self.pregunta.get() else SIDEBAR)

    def seleccionar(self, clave):
        self.pregunta.set(clave)
        for c, b in self._botones.items():
            b.configure(bg=ACENTO if c == clave else SIDEBAR)
        _, texto, usa_materia, usa_objetivo = next(p for p in PREGUNTAS if p[0] == clave)
        self.lbl_titulo.configure(text=texto)
        self.lbl_ayuda.configure(text=AYUDA[clave])
        for w in (self.lbl_materia, self.combo):
            (w.grid if usa_materia else w.grid_remove)()
        for w in (self.lbl_objetivo, self.ent_objetivo):
            (w.grid if usa_objetivo else w.grid_remove)()
        self.btn.configure(text="Consultar" if usa_materia else "Actualizar")
        if usa_materia:
            self.combo.focus_set()
            if not self.materia_var.get():
                self._mostrar(f"Elige una materia (puedes escribir su código o nombre) y pulsa «Consultar».")
                return
        self.consultar()

    def _filtrar(self, evento):
        if evento.keysym in ("Return", "Up", "Down", "Escape", "Tab"):
            return
        t = self.materia_var.get().strip().lower()
        self.combo.configure(values=[m for m in self._todas_las_materias if t in m.lower()]
                             or self._todas_las_materias)

    def _codigo(self):
        t = self.materia_var.get().strip()
        codigo = t.split("—")[0].strip().upper()
        if codigo in self.ctx.G.nodes:
            return codigo
        # intento por nombre exacto o parcial único
        coincide = [m for m in self._todas_las_materias if t.lower() in m.lower()] if t else []
        if len(coincide) == 1:
            return coincide[0].split("—")[0].strip()
        return None

    def consultar(self):
        if not self.ctx:
            return
        clave = self.pregunta.get()
        _, _, usa_materia, usa_objetivo = next(p for p in PREGUNTAS if p[0] == clave)
        codigo = None
        if usa_materia:
            codigo = self._codigo()
            if codigo is None:
                self._mostrar("No encuentro esa materia. Escribe un código como MAT1111 o elige una de la lista.")
                return
            self.materia_var.set(f"{codigo} — {self.ctx.G.nodes[codigo]['nombre']}")
        objetivo = None
        if usa_objetivo:
            try:
                objetivo = float(self.objetivo_var.get().replace(",", "."))
            except ValueError:
                self._mostrar("El promedio objetivo debe ser un número, por ejemplo 3.5.")
                return
            if not 0 <= objetivo <= 5:
                self._mostrar("El promedio objetivo debe estar entre 0 y 5.")
                return
        self.update_idletasks()
        try:
            salida = self._resolver(clave, codigo, objetivo)
        except Exception as e:
            messagebox.showerror("Algo salió mal", f"{type(e).__name__}: {e}")
            return
        if clave == "historial":
            self.texto.pack_forget()
            self.tabla.pack(side="left", fill="both", expand=True)
        else:
            self._mostrar(salida)

    def _resolver(self, clave, codigo, objetivo):
        ctx = self.ctx
        return {
            "resumen": lambda: texto_resumen(ctx),
            "todas": lambda: texto_todas(ctx),
            "proximo": lambda: texto_proximo(ctx),
            "puedo": lambda: texto_puedo(ctx, codigo),
            "retiro": lambda: texto_retiro(ctx, codigo),
            "pierdo": lambda: texto_pierdo(ctx, codigo),
            "nota": lambda: texto_nota(ctx, codigo, objetivo),
            "importancia": lambda: texto_importancia(ctx),
            "booleano": lambda: bo.texto_booleano(ctx.G, codigo),
            "verificar": lambda: texto_verificacion(ctx),
            "historial": lambda: "",
        }[clave]()

    def _mostrar(self, contenido):
        self.tabla.pack_forget()
        self.texto.pack(side="left", fill="both", expand=True)
        self.texto.configure(state="normal")
        self.texto.delete("1.0", "end")
        for linea in contenido.split("\n"):
            etiqueta = ()
            if linea.startswith("Sí:"):
                etiqueta = ("si",)
            elif linea.startswith("No:"):
                etiqueta = ("no",)
            elif linea.endswith(":") and not linea.startswith(" "):
                etiqueta = ("titulo",)
            elif linea.startswith("(*)") or linea.startswith("Ojo:"):
                etiqueta = ("aviso",)
            self.texto.insert("end", linea + "\n", etiqueta)
        self.texto.configure(state="disabled")
        self.texto.yview_moveto(0)


def main(carrera="sistemas", historial=None, datos=None):
    App(carrera, historial, datos).mainloop()


if __name__ == "__main__":
    main()
