import tkinter as tk
import customtkinter as ctk


class RightPanel(ctk.CTkFrame):
    """Panel derecho con pestañas de análisis en dos filas.

    Fila 1: Léxico · Sintáctico · Semántico  +  ✕
    Fila 2: Hash Table · Cód. Intermedio
    """

    ROW1_NAMES = ["Léxico", "Sintáctico", "Semántico"]
    ROW2_NAMES = ["Hash Table", "Cód. Intermedio"]

    def __init__(self, parent, colors, **kwargs):
        super().__init__(
            parent,
            fg_color=colors["activity_bg"],
            width=280,
            corner_radius=0,
            border_width=1,
            border_color=colors["hover"],
            **kwargs,
        )
        self.colors = colors
        self.visible = False
        self._tabs = {}
        self._current_tab = None
        self.pack_propagate(False)

        self._build_ui()

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------
    def _build_ui(self):
        # Fila 1
        row1 = ctk.CTkFrame(self, fg_color=self.colors["title_bg"], height=28, corner_radius=0)
        row1.pack(fill=tk.X)
        row1.pack_propagate(False)

        for name in self.ROW1_NAMES:
            self._add_tab_label(row1, name)

        # Botón cerrar
        close_btn = ctk.CTkLabel(
            row1, text="\u2715", fg_color="transparent",
            text_color=self.colors["comments"], font=("Consolas", 13), width=28,
        )
        close_btn.pack(side=tk.RIGHT, padx=(0, 4), fill=tk.Y)
        close_btn.bind("<Button-1>", lambda e: self.hide())
        close_btn.bind("<Enter>", lambda e: close_btn.configure(fg_color="#e81123", text_color=self.colors["fg"]))
        close_btn.bind("<Leave>", lambda e: close_btn.configure(fg_color="transparent", text_color=self.colors["comments"]))

        # Fila 2
        row2 = ctk.CTkFrame(self, fg_color=self.colors["title_bg"], height=28, corner_radius=0)
        row2.pack(fill=tk.X)
        row2.pack_propagate(False)

        for name in self.ROW2_NAMES:
            self._add_tab_label(row2, name)

        # Separador
        ctk.CTkFrame(self, fg_color=self.colors["hover"], height=1, corner_radius=0).pack(fill=tk.X)

        # Activar primera pestaña
        self.set_tab(self.ROW1_NAMES[0])

    def _add_tab_label(self, parent_row, name):
        lbl = ctk.CTkLabel(
            parent_row, text=name, fg_color="transparent",
            text_color=self.colors["comments"], font=("Segoe UI", 11),
            padx=8, pady=2,
        )
        lbl.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 2))
        lbl.bind("<Button-1>", lambda e, n=name: self.set_tab(n))
        lbl.bind("<Enter>", lambda e, w=lbl: w.configure(text_color=self.colors["fg"]))
        lbl.bind("<Leave>", lambda e, w=lbl, n=name: w.configure(
            text_color=self.colors["fg"] if n == self._current_tab else self.colors["comments"]
        ))

        content = ctk.CTkFrame(self, fg_color=self.colors["bg"], corner_radius=0)
        self._tabs[name] = (lbl, content)

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

    def show(self):
        """Muestra el panel."""
        if not self.visible:
            self.pack(side=tk.RIGHT, fill=tk.Y)
            self.visible = True

    def hide(self):
        """Oculta el panel."""
        if self.visible:
            self.pack_forget()
            self.visible = False

    def toggle(self):
        if self.visible:
            self.hide()
        else:
            self.show()

    def get_tab_content(self, name):
        """Devuelve el frame de contenido de una pestaña."""
        if name in self._tabs:
            return self._tabs[name][1]
        return None
