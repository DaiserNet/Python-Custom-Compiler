import tkinter as tk
import customtkinter as ctk

from app.core.lexer import LexicalAnalyzer
from app.core.tokens import token_color_group

# Mantenemos CustomText como tk.Text puro para no romper el proxy y dlineinfo
class CustomText(tk.Text):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

    def _proxy(self, command, *args):
        cmd = (self._orig, command) + args
        try:
            result = self.tk.call(cmd)
        except tk.TclError:
            result = ""

        if command in ("insert", "delete", "replace", "mark"):
            self.event_generate("<<Change>>", when="tail")

        return result

# Mantenemos Canvas puro para mejor rendimiento al dibujar líneas
class LineNumberCanvas(tk.Canvas):
    def __init__(self, parent, text_widget, colors, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.text_widget = text_widget
        self.colors = colors
        self.config(bg=colors["activity_bg"], highlightthickness=0)
        self.font = ("Consolas", 12)

    def redraw(self, *args):
        self.delete("all")

        i = self.text_widget.index("@0,0")
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            linenum = str(i).split(".")[0]
            
            current_line = self.text_widget.index(tk.INSERT).split(".")[0]
            if linenum == current_line:
                color = self.colors["strings"] 
            else:
                color = self.colors["comments"]

            self.create_text(
                self.winfo_width() - 10, 
                y, 
                anchor="ne", 
                text=linenum, 
                font=self.font, 
                fill=color
            )
            i = self.text_widget.index(f"{i}+1line")

# Actualizamos a CTkFrame
class CodeEditorFrame(ctk.CTkFrame):
    def __init__(self, parent, colors, on_cursor_move=None, on_text_change=None, *args, **kwargs):
        super().__init__(parent, fg_color=colors["bg"], corner_radius=0, *args, **kwargs)
        self.colors = colors
        self.on_cursor_move = on_cursor_move
        self.on_text_change = on_text_change
        self.lexer = LexicalAnalyzer()
        # 1. Creamos la Scrollbar Horizontal primero y la ponemos abajo
        # Usamos un comando temporal, lo actualizaremos cuando creemos el texto
        self.h_scrollbar = ctk.CTkScrollbar(self, orientation="horizontal")
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # 2. Creamos un "Contenedor Principal" para lo que va arriba de la scrollbar horizontal
        self.text_area_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.text_area_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 3. Dentro del contenedor principal, la Scrollbar Vertical a la derecha
        self.scrollbar = ctk.CTkScrollbar(self.text_area_container, orientation="vertical")
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 4. Los números de línea a la izquierda
        self.linenumbers = LineNumberCanvas(self.text_area_container, None, colors, width=40)
        self.linenumbers.pack(side=tk.LEFT, fill=tk.Y)

        # 5. El texto ocupa el resto del espacio en el centro
        self.text = CustomText(
            self.text_area_container,
            bg=self.colors["bg"], 
            fg=self.colors["variables"], 
            insertbackground=self.colors["fg"], 
            wrap=tk.NONE, # Sin ajuste de línea
            font=("Consolas", 12),
            bd=0,
            highlightthickness=0
        )
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.linenumbers.text_widget = self.text
        self._configure_syntax_tags()

        # 6. CONECTAMOS TODO (Ahora que self.text ya existe)
        def _on_yscroll(*args):
            self.scrollbar.set(*args)
            self._on_change()
            
        def _on_xscroll(*args):
            self.h_scrollbar.set(*args)
            self._on_change()

        # Le decimos al texto cómo actualizar las barras
        self.text.configure(yscrollcommand=_on_yscroll, xscrollcommand=_on_xscroll)
        
        # Le decimos a las barras cómo mover el texto
        self.scrollbar.configure(command=self.text.yview)
        self.h_scrollbar.configure(command=self.text.xview)

        # 7. Eventos
        self.text.bind("<<Change>>", self._on_change)
        self.text.bind("<Configure>", self._on_change)
        self.text.bind("<KeyRelease>", self._on_change)
        self.text.bind("<ButtonRelease-1>", self._on_change)
        self.text.bind("<B1-Motion>", self._on_change)
        self.text.bind("<MouseWheel>", self._on_change)

    def _configure_syntax_tags(self):
        self.text.tag_configure("token_color_1", foreground=self.colors.get("token_color_1", "#61afef"))
        self.text.tag_configure("token_color_2", foreground=self.colors.get("token_color_2", "#8be9fd"))
        self.text.tag_configure("token_color_3", foreground=self.colors.get("token_color_3", "#6272a4"))
        self.text.tag_configure("token_color_4", foreground=self.colors.get("token_color_4", "#ff79c6"))
        self.text.tag_configure("token_color_5", foreground=self.colors.get("token_color_5", "#ffb86c"))
        self.text.tag_configure("token_color_6", foreground=self.colors.get("token_color_6", "#50fa7b"))
        self.text.tag_configure(
            "lexical_error_marker",
            foreground="#ff5555",
            underline=True,
        )

    def _apply_syntax_highlighting(self):
        source = self.text.get("1.0", "end-1c")
        for color_tag in (
            "token_color_1",
            "token_color_2",
            "token_color_3",
            "token_color_4",
            "token_color_5",
            "token_color_6",
        ):
            self.text.tag_remove(color_tag, "1.0", tk.END)

        for token in self.lexer.tokenize(source):
            group = token_color_group(token.token_type)
            if group is None:
                continue
            start_index = f"1.0+{token.start}c"
            end_index = f"1.0+{token.end}c"
            self.text.tag_add(f"token_color_{group}", start_index, end_index)

    def _on_cursor_move(self, event=None):
        """Obtiene la posición actual y llama al callback si existe."""
        cursor_index = self.text.index(tk.INSERT)
        line, col = cursor_index.split('.')
        line = int(line)
        col = int(col) + 1   # tkinter cuenta desde 0, mostrar desde 1
        if self.on_cursor_move:
            self.on_cursor_move(line, col)

    def clear_lexical_error_marks(self):
        self.text.tag_remove("lexical_error_marker", "1.0", tk.END)

    def apply_lexical_errors(self, errors):
        self.clear_lexical_error_marks()
        for error in errors:
            index = self._error_to_text_index(error)
            if index is None:
                continue
            end_index = self.text.index(f"{index}+1c")
            self.text.tag_add("lexical_error_marker", index, end_index)

        # Keep lexical errors visually above syntax colors.
        self.text.tag_raise("lexical_error_marker")

    def focus_on_lexical_error(self, error):
        index = self._error_to_text_index(error)
        if index is None:
            return
        self.text.mark_set(tk.INSERT, index)
        self.text.see(index)
        self._on_cursor_move()

    def _error_to_text_index(self, error):
        try:
            line = max(int(getattr(error, "line", 1)), 1)
            column = max(int(getattr(error, "column", 1)) - 1, 0)
            index = f"{line}.{column}"
            self.text.index(index)
            return index
        except Exception:
            return None

    def _on_change(self, event=None):
        self.text.update_idletasks()
        self._apply_syntax_highlighting()
        self.linenumbers.redraw()
        self._on_cursor_move()
        if self.on_text_change:
            self.on_text_change(self, self.text.get("1.0", "end-1c"))