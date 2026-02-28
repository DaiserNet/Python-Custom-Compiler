import tkinter as tk
import customtkinter as ctk


class SearchPanel(ctk.CTkFrame):
    """Panel lateral de búsqueda (solo visual)."""

    def __init__(self, parent, colors, **kwargs):
        super().__init__(parent, fg_color=colors["activity_bg"], width=250, corner_radius=0, **kwargs)
        self.colors = colors
        self.pack_propagate(False)

        self._details_open = False
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        # Encabezado
        header = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0, height=30)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="SEARCH", fg_color="transparent",
            text_color=self.colors["menu_fg"], font=("Segoe UI", 11), anchor="w"
        ).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        # Separador
        ctk.CTkFrame(self, fg_color=self.colors["hover"], height=1, corner_radius=0).pack(fill=tk.X)

        # Área de búsqueda
        search_area = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        search_area.pack(fill=tk.X, padx=8, pady=(10, 0))

        search_row = ctk.CTkFrame(search_area, fg_color="transparent", corner_radius=0)
        search_row.pack(fill=tk.X)

        # Flecha colapsable
        self._toggle_arrow = ctk.CTkLabel(
            search_row, text="\u25B7", fg_color="transparent",
            text_color=self.colors["menu_fg"], font=("Segoe UI", 12), width=20
        )
        self._toggle_arrow.pack(side=tk.LEFT)
        self._toggle_arrow.bind("<Button-1>", lambda e: self._toggle_details())

        # Campo de búsqueda
        self.search_entry = ctk.CTkEntry(
            search_row, placeholder_text="Search",
            fg_color=self.colors["bg"], border_color=self.colors["hover"],
            text_color=self.colors["fg"], placeholder_text_color=self.colors["comments"],
            font=("Segoe UI", 12), height=28, corner_radius=4
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

        # Opciones (Aa, ab, .*)
        options_frame = ctk.CTkFrame(search_area, fg_color="transparent", corner_radius=0)
        options_frame.pack(fill=tk.X, pady=(4, 0))

        ctk.CTkLabel(options_frame, text="", fg_color="transparent").pack(side=tk.LEFT, fill=tk.X, expand=True)

        for text, _ in [("Aa", "Match Case"), ("ab", "Match Whole Word"), (".*", "Use Regular Expression")]:
            opt = ctk.CTkLabel(
                options_frame, text=text, fg_color="transparent",
                text_color=self.colors["comments"], font=("Consolas", 11, "bold"),
                width=28, height=22,
            )
            opt.pack(side=tk.LEFT, padx=1)
            opt.bind("<Enter>", lambda e, w=opt: w.configure(fg_color=self.colors["hover"], text_color=self.colors["fg"]))
            opt.bind("<Leave>", lambda e, w=opt: w.configure(fg_color="transparent", text_color=self.colors["comments"]))

        more_btn = ctk.CTkLabel(
            options_frame, text="···", fg_color="transparent",
            text_color=self.colors["comments"], font=("Consolas", 11, "bold"),
            width=22, height=22,
        )
        more_btn.pack(side=tk.LEFT, padx=(4, 0))
        more_btn.bind("<Enter>", lambda e: more_btn.configure(fg_color=self.colors["hover"], text_color=self.colors["fg"]))
        more_btn.bind("<Leave>", lambda e: more_btn.configure(fg_color="transparent", text_color=self.colors["comments"]))

        # Panel expandible de detalles
        self._details_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)

    def _toggle_details(self):
        if self._details_open:
            self._details_frame.pack_forget()
            self._toggle_arrow.configure(text="\u25B7")
            self._details_open = False
        else:
            self._details_frame.pack(fill=tk.X, padx=8, pady=(6, 0), after=self.search_entry.master.master)
            self._toggle_arrow.configure(text="\u25BD")
            self._details_open = True
