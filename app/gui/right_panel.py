import tkinter as tk
import customtkinter as ctk

from app.core.tokens import TokenType


class RightPanel(ctk.CTkFrame):
    """Panel derecho con pestañas de análisis en dos filas.

    Fila 1: Léxico · Sintáctico · Semántico  +  ✕
    Fila 2: Hash Table · Cód. Intermedio
    """

    ROW1_NAMES = ["Léxico", "Sintáctico", "Semántico"]
    ROW2_NAMES = ["Hash Table", "Cód. Intermedio"]
    MAX_VISIBLE_TOKENS = 400

    TABLE_INDEX_WIDTH = 4
    TABLE_TYPE_WIDTH = 18
    TABLE_LEXEME_WIDTH = 30
    TABLE_LINE_WIDTH = 5
    TABLE_COLUMN_WIDTH = 7

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
        self._lexical_trace_box = None
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

        # Contenido del analisis lexico
        self._build_lexical_tab()

        # Activar primera pestaña
        self.set_tab(self.ROW1_NAMES[0])

    def _build_lexical_tab(self):
        content = self.get_tab_content("Léxico")
        if content is None:
            return

        title = ctk.CTkLabel(
            content,
            text="Ejecucion del analizador lexico",
            text_color=self.colors["comments"],
            anchor="w",
            font=("Segoe UI", 11),
        )
        title.pack(fill=tk.X, padx=8, pady=(8, 4))

        self._lexical_trace_box = ctk.CTkTextbox(
            content,
            fg_color=self.colors["bg"],
            text_color=self.colors["fg"],
            border_width=0,
            corner_radius=0,
            wrap="none",
            font=("Consolas", 11),
        )
        self._lexical_trace_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self._set_textbox_value(self._lexical_trace_box, "Sin analisis lexico ejecutado.")

    @staticmethod
    def _set_textbox_value(textbox, content):
        textbox.configure(state="normal")
        textbox.delete("1.0", tk.END)
        textbox.insert("1.0", content)
        textbox.configure(state="disabled")

    @staticmethod
    def _truncate_cell(value, width):
        if len(value) <= width:
            return value
        if width <= 3:
            return value[:width]
        return f"{value[:width - 3]}..."

    def _format_lexical_trace(self, tokens):
        header = (
            f"{'#':>{self.TABLE_INDEX_WIDTH}} | "
            f"{'TIPO':<{self.TABLE_TYPE_WIDTH}} | "
            f"{'LEXEMA':<{self.TABLE_LEXEME_WIDTH}} | "
            f"{'LINEA':>{self.TABLE_LINE_WIDTH}} | "
            f"{'COLUMNA':>{self.TABLE_COLUMN_WIDTH}}"
        )
        separator = "-" * len(header)

        lines = [
            "Tokens",
            f"Tokens mostrados: {len(tokens)}",
            "",
            header,
            separator,
        ]

        for idx, token in enumerate(tokens[:self.MAX_VISIBLE_TOKENS], start=1):
            token_type = self._truncate_cell(str(token.token_type.value), self.TABLE_TYPE_WIDTH)
            escaped_lexeme = token.lexeme.replace("\n", "\\n").replace("\t", "\\t")
            lexeme = self._truncate_cell(f"'{escaped_lexeme}'", self.TABLE_LEXEME_WIDTH)

            lines.append(
                f"{idx:>{self.TABLE_INDEX_WIDTH}} | "
                f"{token_type:<{self.TABLE_TYPE_WIDTH}} | "
                f"{lexeme:<{self.TABLE_LEXEME_WIDTH}} | "
                f"{token.line:>{self.TABLE_LINE_WIDTH}} | "
                f"{token.column:>{self.TABLE_COLUMN_WIDTH}}"
            )

        if len(tokens) > self.MAX_VISIBLE_TOKENS:
            omitted = len(tokens) - self.MAX_VISIBLE_TOKENS
            lines.append("")
            lines.append(f"... {omitted} tokens omitidos ...")

        return "\n".join(lines)

    def _get_lexical_trace_text_widget(self):
        """Return the underlying tk.Text used by CTkTextbox for tag operations."""
        if self._lexical_trace_box is None:
            return None

        native_text = getattr(self._lexical_trace_box, "_textbox", None)
        if native_text is not None:
            return native_text

        if isinstance(self._lexical_trace_box, tk.Text):
            return self._lexical_trace_box

        return None

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

    def set_lexical_trace(self, analysis_result):
        """Muestra la traza de tokens del analizador lexico sin comentarios."""
        if self._lexical_trace_box is None:
            return

        if analysis_result is None:
            self._set_textbox_value(self._lexical_trace_box, "Sin analisis lexico ejecutado.")
            return

        tokens = getattr(analysis_result, "tokens", [])
        filtered_tokens = [
            token for token in tokens
            if token.token_type not in (TokenType.COMMENT_SINGLE, TokenType.COMMENT_MULTI)
        ]
        content = self._format_lexical_trace(filtered_tokens)

        text_widget = self._get_lexical_trace_text_widget()
        if text_widget is None:
            self._set_textbox_value(self._lexical_trace_box, content)
            return

        text_widget.configure(state="normal")
        text_widget.delete("1.0", tk.END)

        text_widget.insert(tk.END, content)

        text_widget.configure(state="disabled")
