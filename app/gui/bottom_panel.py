import tkinter as tk
import customtkinter as ctk


class BottomPanel(ctk.CTkFrame):
    """Panel inferior con pestañas de errores y resultados.

    Se crea oculto; llamar a show() / hide() para controlar visibilidad.
    """

    TAB_NAMES = ["Error Léxico", "Error Sintáctico", "Error Semántico", "Resultados"]

    def __init__(self, parent, colors, **kwargs):
        super().__init__(
            parent,
            fg_color=colors["title_bg"],
            height=200,
            corner_radius=0,
            border_width=1,
            border_color=colors["hover"],
            **kwargs,
        )
        self.colors = colors
        self.visible = False
        self._tabs = {}
        self._current_tab = None
        self._lexical_error_box = None

        self._build_ui()

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------
    def _build_ui(self):
        # Barra de pestañas
        tab_bar = ctk.CTkFrame(self, fg_color=self.colors["title_bg"], height=32, corner_radius=0)
        tab_bar.pack(fill=tk.X)
        tab_bar.pack_propagate(False)

        for name in self.TAB_NAMES:
            lbl = ctk.CTkLabel(
                tab_bar, text=name, fg_color="transparent",
                text_color=self.colors["comments"], font=("Segoe UI", 12),
                padx=6, pady=4,
            )
            lbl.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 2))
            lbl.bind("<Button-1>", lambda e, n=name: self.set_tab(n))
            lbl.bind("<Enter>", lambda e, w=lbl: w.configure(text_color=self.colors["fg"]))
            lbl.bind("<Leave>", lambda e, w=lbl, n=name: w.configure(
                text_color=self.colors["fg"] if n == self._current_tab else self.colors["comments"]
            ))

            content = ctk.CTkFrame(self, fg_color=self.colors["bg"], corner_radius=0)
            self._tabs[name] = (lbl, content)

        # Botón cerrar (✕)
        close_btn = ctk.CTkLabel(
            tab_bar, text="✕", fg_color="transparent",
            text_color=self.colors["comments"], font=("Consolas", 13), width=28,
        )
        close_btn.pack(side=tk.RIGHT, padx=(0, 6), fill=tk.Y)
        close_btn.bind("<Button-1>", lambda e: self.hide())
        close_btn.bind("<Enter>", lambda e: close_btn.configure(fg_color="#e81123", text_color=self.colors["fg"]))
        close_btn.bind("<Leave>", lambda e: close_btn.configure(fg_color="transparent", text_color=self.colors["comments"]))

        # Botón ···
        more_btn = ctk.CTkLabel(
            tab_bar, text="···", fg_color="transparent",
            text_color=self.colors["comments"], font=("Consolas", 14, "bold"), width=28,
        )
        more_btn.pack(side=tk.RIGHT, padx=2, fill=tk.Y)
        more_btn.bind("<Enter>", lambda e: more_btn.configure(fg_color=self.colors["hover"], text_color=self.colors["fg"]))
        more_btn.bind("<Leave>", lambda e: more_btn.configure(fg_color="transparent", text_color=self.colors["comments"]))

        # Separador
        ctk.CTkFrame(self, fg_color=self.colors["hover"], height=1, corner_radius=0).pack(fill=tk.X)

        # Contenido de pestañas de analisis
        self._build_lexical_error_tab()
        self._build_syntactic_error_tab()

        # Activar primera pestaña
        self.set_tab(self.TAB_NAMES[0])

    def _build_lexical_error_tab(self):
        content = self.get_tab_content("Error Léxico")
        if content is None:
            return

        header = ctk.CTkLabel(
            content,
            text="Errores detectados por el analizador léxico",
            text_color=self.colors["comments"],
            anchor="w",
            font=("Segoe UI", 11),
        )
        header.pack(fill=tk.X, padx=8, pady=(8, 4))

        self._lexical_error_box = ctk.CTkTextbox(
            content,
            fg_color=self.colors["bg"],
            text_color=self.colors["fg"],
            border_width=0,
            corner_radius=0,
            wrap="none",
            font=("Consolas", 11),
        )
        self._lexical_error_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self._set_textbox_value(self._lexical_error_box, "Sin analisis lexico ejecutado.")

    @staticmethod
    def _set_textbox_value(textbox, content):
        textbox.configure(state="normal")
        textbox.delete("1.0", tk.END)
        textbox.insert("1.0", content)
        textbox.configure(state="disabled")

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def set_tab(self, name):
        """Cambia la pestaña activa."""
        if self._current_tab and self._current_tab in self._tabs:
            old_lbl, old_content = self._tabs[self._current_tab]
            old_lbl.configure(text_color=self.colors["comments"])
            old_content.pack_forget()

        if name in self._tabs:
            lbl, content = self._tabs[name]
            lbl.configure(text_color=self.colors["fg"])
            content.pack(fill=tk.BOTH, expand=True)
            self._current_tab = name

    def show(self, height=200):
        """Muestra el panel con la altura indicada."""
        if not self.visible:
            self.pack(side=tk.BOTTOM, fill=tk.X)
            self.configure(height=height)
            self.pack_propagate(False)
            self.visible = True

    def hide(self):
        """Oculta el panel."""
        if self.visible:
            self.pack_forget()
            self.visible = False

    def toggle(self, height=200):
        """Alterna visibilidad."""
        if self.visible:
            self.hide()
        else:
            self.show(height)

    def get_tab_content(self, name):
        """Devuelve el frame de contenido de una pestaña (para agregar widgets)."""
        if name in self._tabs:
            return self._tabs[name][1]
        return None

    def set_lexical_errors(self, errors):
        """Renderiza los errores léxicos con formato de linea y columna."""
        if self._lexical_error_box is None:
            return

        if not errors:
            self._set_textbox_value(self._lexical_error_box, "Sin errores lexicos.")
            return

        lines = []
        for idx, error in enumerate(errors, start=1):
            if isinstance(error, dict):
                line = error.get("line", 0)
                column = error.get("column", 0)
                message = error.get("message", "Error lexico")
                lexeme = error.get("lexeme", "")
            else:
                line = getattr(error, "line", 0)
                column = getattr(error, "column", 0)
                message = getattr(error, "message", "Error lexico")
                lexeme = getattr(error, "lexeme", "")

            lines.append(
                f"{idx}. Linea {line}, columna {column}: {message} [lexema: {lexeme}]"
            )

        self._set_textbox_value(self._lexical_error_box, "\n".join(lines))

    def _build_syntactic_error_tab(self):
        content = self.get_tab_content("Error Sintáctico")
        if content is None:
            return

        header = ctk.CTkLabel(
            content,
            text="Errores detectados por el analizador sintáctico",
            text_color=self.colors["comments"],
            anchor="w",
            font=("Segoe UI", 11),
        )
        header.pack(fill=tk.X, padx=8, pady=(8, 4))

        self._syntactic_error_box = ctk.CTkTextbox(
            content,
            fg_color=self.colors["bg"],
            text_color="#e81123",  # Color rojo para resaltar que es un error
            border_width=0,
            corner_radius=0,
            wrap="none",
            font=("Consolas", 11),
        )
        self._syntactic_error_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self._set_textbox_value(self._syntactic_error_box, "Sin análisis sintáctico ejecutado.")

    def set_syntactic_errors(self, errors):
        """Renderiza los errores sintácticos en la consola inferior."""
        if getattr(self, "_syntactic_error_box", None) is None:
            return

        if not errors:
            self._set_textbox_value(self._syntactic_error_box, "Sin errores sintácticos. Árbol AST generado con éxito.")
            return

        lines = []
        for idx, error in enumerate(errors, start=1):
            # Adaptar según cómo estructures tus objetos de error sintáctico en parser.py
            if isinstance(error, dict):
                line = error.get("line", "?")
                column = error.get("column", "?")
                message = error.get("message", "Error de sintaxis")
            else:
                line = getattr(error, "line", "?")
                column = getattr(error, "column", "?")
                message = getattr(error, "message", "Error de sintaxis")

            lines.append(f"{idx}. Línea {line}, columna {column}: {message}")

        self._set_textbox_value(self._syntactic_error_box, "\n".join(lines))
        # Opcional: Mostrar el panel inferior automáticamente si hay errores
        self.show()
        self.set_tab("Error Sintáctico")
