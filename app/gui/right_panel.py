import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

from app.core.tokens import TokenType
from app.core.parser import ASTNode


class RightPanel(ctk.CTkFrame):
    """Panel derecho con pestañas de análisis en dos filas.

    Fila 1: Léxico · Sintáctico · Semántico  +  ✕
    Fila 2: Hash Table · Cód. Intermedio
    """

    ROW1_NAMES = ["Léxico", "Sintáctico", "Semántico"]
    ROW2_NAMES = ["Hash Table", "Cód. Intermedio"]
    MAX_VISIBLE_TOKENS = 400
    DEFAULT_WIDTH = 280
    MIN_WIDTH = 220
    MAX_WIDTH = 560
    MIN_EDITOR_WIDTH = 360
    RESIZER_WIDTH = 5

    TABLE_INDEX_WIDTH = 4
    TABLE_TYPE_WIDTH = 18
    TABLE_LEXEME_WIDTH = 30
    TABLE_LINE_WIDTH = 5
    TABLE_COLUMN_WIDTH = 7

    def __init__(self, parent, colors, **kwargs):
        super().__init__(
            parent,
            fg_color=colors["activity_bg"],
            width=self.DEFAULT_WIDTH,
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
        self._resize_start_x = None
        self._resize_start_width = self.DEFAULT_WIDTH
        self._resize_handle = None
        self.pack_propagate(False)

        if self.master is not None:
            self.master.bind("<Configure>", self._on_parent_configure, add="+")

        self._build_ui()
        self._clamp_width_to_bounds()

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------
    def _build_ui(self):
        self._resize_handle = ctk.CTkFrame(
            self,
            fg_color=self.colors["hover"],
            width=self.RESIZER_WIDTH,
            corner_radius=0,
        )
        self._resize_handle.pack(side=tk.LEFT, fill=tk.Y)
        self._resize_handle.pack_propagate(False)
        self._resize_handle.bind("<ButtonPress-1>", self._on_resize_start)
        self._resize_handle.bind("<B1-Motion>", self._on_resize_drag)
        self._resize_handle.bind("<ButtonRelease-1>", self._on_resize_end)
        self._resize_handle.bind("<Enter>", self._on_resize_handle_enter)
        self._resize_handle.bind("<Leave>", self._on_resize_handle_leave)

        try:
            self._resize_handle.configure(cursor="sb_h_double_arrow")
        except tk.TclError:
            pass

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
        self._build_syntactic_tab()

        # Activar primera pestaña
        self.set_tab(self.ROW1_NAMES[0])

    def _get_current_width(self):
        try:
            return int(float(self.cget("width")))
        except (TypeError, ValueError):
            return max(self.winfo_width(), self.DEFAULT_WIDTH)

    def _get_width_bounds(self):
        min_width = self.MIN_WIDTH
        max_width = self.MAX_WIDTH

        if self.master is not None:
            parent_width = self.master.winfo_width()
            if parent_width > (self.MIN_EDITOR_WIDTH + self.MIN_WIDTH):
                max_width = min(max_width, parent_width - self.MIN_EDITOR_WIDTH)

        if max_width < min_width:
            max_width = min_width

        return min_width, max_width

    def _set_panel_width(self, width):
        min_width, max_width = self._get_width_bounds()
        clamped_width = max(min_width, min(max_width, int(width)))
        current_width = self._get_current_width()

        if clamped_width != current_width:
            self.configure(width=clamped_width)

    def _clamp_width_to_bounds(self):
        self._set_panel_width(self._get_current_width())

    def _on_parent_configure(self, _event):
        self._clamp_width_to_bounds()

    def _on_resize_start(self, event):
        self._resize_start_x = event.x_root
        self._resize_start_width = self._get_current_width()
        self._resize_handle.configure(fg_color=self.colors["comments"])

    def _on_resize_drag(self, event):
        if self._resize_start_x is None:
            return

        delta = self._resize_start_x - event.x_root
        self._set_panel_width(self._resize_start_width + delta)

    def _on_resize_end(self, _event):
        self._resize_start_x = None
        self._resize_handle.configure(fg_color=self.colors["hover"])

    def _on_resize_handle_enter(self, _event):
        if self._resize_start_x is None:
            self._resize_handle.configure(fg_color=self.colors["comments"])

    def _on_resize_handle_leave(self, _event):
        if self._resize_start_x is None:
            self._resize_handle.configure(fg_color=self.colors["hover"])

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
            self._clamp_width_to_bounds()
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

    def _build_syntactic_tab(self):
        content = self.get_tab_content("Sintáctico")
        if content is None:
            return

        title = ctk.CTkLabel(
            content,
            text="Árbol Sintáctico (CST / AST)",
            text_color=self.colors["comments"],
            anchor="w",
            font=("Segoe UI", 11),
        )
        title.pack(fill=tk.X, padx=8, pady=(8, 4))

        # ------------------------------------------------------------------
        # Configuración de Estilos para el Treeview (Para que cuadre con tu tema)
        # ------------------------------------------------------------------
        style = ttk.Style()
        style.theme_use("clam")  # El tema 'clam' permite modificar herencias visuales con éxito
        
        style.configure(
            "Treeview",
            background=self.colors["bg"],
            foreground=self.colors["fg"],
            fieldbackground=self.colors["bg"],
            font=("Segoe UI", 11),
            rowheight=22,
            borderwidth=0,
        )
        # Cambiar el color de la fila seleccionada
        style.map(
            "Treeview",
            background=[("selected", self.colors["hover"])],
            foreground=[("selected", "#ffffff")],
        )
        # Quitar bordes de encabezados ocultos si los hubiera
        style.configure("Treeview.Heading", background=self.colors["title_bg"], borderwidth=0)

        # ------------------------------------------------------------------
        # Creación del Treeview
        # ------------------------------------------------------------------
        # Usamos show="tree" para ocultar la columna de encabezados vacía por defecto
        self._tree_view = ttk.Treeview(content, show="tree", selectmode="browse")
        self._tree_view.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        # Insertar mensaje inicial por defecto
        self._tree_view.insert("", "end", text="Sin análisis sintáctico ejecutado.")

    def set_syntactic_tree(self, tree_data):
        """Renderiza el árbol sintáctico AST.

        Puede recibir un objeto ASTNode o un string con un mensaje de error.
        """
        if getattr(self, "_tree_view", None) is None:
            return

        # Limpiar por completo el Treeview antes de redibujar
        self._tree_view.delete(*self._tree_view.get_children())

        # Si lo que recibimos es un String (es un error o advertencia)
        if isinstance(tree_data, str):
            self._tree_view.insert("", "end", text=tree_data)
            return

        # Si es un objeto ASTNode válido, lo poblamos recursivamente
        if isinstance(tree_data, ASTNode):
            self._populate_tree_node("", tree_data)
        elif tree_data is not None:
            # Fallback para cualquier otro tipo de nodo
            self._tree_view.insert("", "end", text=str(tree_data))
        else:
            self._tree_view.insert("", "end", text="Árbol vacío o inválido.")

    def _populate_tree_node(self, parent_id, node):
        """Método recursivo para renderizar un ASTNode en el Treeview colapsable."""
        if not isinstance(node, ASTNode):
            # Nodo no reconocido — insertar como texto plano
            self._tree_view.insert(parent_id, "end", text=str(node))
            return

        # Construir la etiqueta del nodo
        label = node.node_type
        if node.value is not None:
            label = f"{node.node_type}: {node.value}"

        # Los nodos con hijos se abren por defecto para ver la estructura
        has_children = len(node.children) > 0
        current_id = self._tree_view.insert(
            parent_id, "end", text=label, open=has_children
        )

        # Recorrer recursivamente todos los hijos
        for child in node.children:
            self._populate_tree_node(current_id, child)