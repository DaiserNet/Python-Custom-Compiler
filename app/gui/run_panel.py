import tkinter as tk
import customtkinter as ctk


class RunPanel(ctk.CTkFrame):
    """Panel lateral de Run and Debug con botón 'Ejecutar y Compilar'.

    on_run() se invoca al presionar el botón.
    """

    def __init__(self, parent, colors, on_run=None, **kwargs):
        super().__init__(parent, fg_color=colors["activity_bg"], width=250, corner_radius=0, **kwargs)
        self.colors = colors
        self._on_run = on_run
        self.pack_propagate(False)

        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        # Encabezado
        header = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0, height=30)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="RUN AND DEBUG", fg_color="transparent",
            text_color=self.colors["menu_fg"], font=("Segoe UI", 11), anchor="w"
        ).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        more_btn = ctk.CTkLabel(
            header, text="···", fg_color="transparent",
            text_color=self.colors["comments"], font=("Consolas", 14, "bold"), width=28,
        )
        more_btn.pack(side=tk.RIGHT, padx=8, fill=tk.Y)
        more_btn.bind("<Enter>", lambda e: more_btn.configure(fg_color=self.colors["hover"], text_color=self.colors["fg"]))
        more_btn.bind("<Leave>", lambda e: more_btn.configure(fg_color="transparent", text_color=self.colors["comments"]))

        # Separador
        ctk.CTkFrame(self, fg_color=self.colors["hover"], height=1, corner_radius=0).pack(fill=tk.X)

        # Sección RUN colapsable
        run_header = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0, height=28)
        run_header.pack(fill=tk.X, pady=(4, 0))
        run_header.pack_propagate(False)

        ctk.CTkLabel(
            run_header, text="\u2304   RUN", fg_color="transparent",
            text_color=self.colors["fg"], font=("Segoe UI", 11, "bold"), anchor="w"
        ).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        # Contenido
        content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        content.pack(fill=tk.X, padx=12, pady=(10, 0))

        self.run_button = ctk.CTkButton(
            content, text="Ejecutar y Compilar",
            fg_color=self.colors["hover"], hover_color=self.colors["comments"],
            text_color=self.colors["fg"], font=("Segoe UI", 13),
            height=32, corner_radius=4,
            command=self._fire_run,
        )
        self.run_button.pack(fill=tk.X, pady=(4, 0))

    def _fire_run(self):
        if self._on_run:
            self._on_run()
