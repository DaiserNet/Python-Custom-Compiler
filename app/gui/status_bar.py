import tkinter as tk
import customtkinter as ctk

class StatusBar(ctk.CTkFrame):
    """Barra de estado inferior que muestra línea/columna e información adicional."""
    def __init__(self, parent, colors, **kwargs):
        super().__init__(parent, fg_color=colors["title_bg"], height=25, corner_radius=0, **kwargs)
        self.colors = colors
        self.pack_propagate(False)

        # Etiqueta para línea y columna (alineada a la derecha)
        self.cursor_label = ctk.CTkLabel(
            self,
            text="Ln 1, Col 1",
            fg_color="transparent",
            text_color=colors["menu_fg"],
            font=("Consolas", 11),
            anchor="e"
        )
        self.cursor_label.pack(side=tk.RIGHT, padx=10)

        # Etiqueta para información adicional (ej. tipo de archivo)
        self.info_label = ctk.CTkLabel(
            self,
            text="Chimera IDE",
            fg_color="transparent",
            text_color=colors["comments"],
            font=("Segoe UI", 11),
            anchor="w"
        )
        self.info_label.pack(side=tk.LEFT, padx=10)

    def update_cursor_position(self, line, col):
        """Actualiza el texto de línea y columna."""
        self.cursor_label.configure(text=f"Ln {line}, Col {col}")

    def update_file_type(self, file_ext):
        """Muestra la extensión del archivo activo (opcional)."""
        self.info_label.configure(text=file_ext if file_ext else "Chimera IDE")