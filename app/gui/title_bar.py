import tkinter as tk
import customtkinter as ctk


class TitleBar(ctk.CTkFrame):
    """Barra de título personalizada con menús y controles de ventana.

    callbacks esperados (dict):
        start_move, do_move, minimize, maximize, close,
        new_file, open_file, close_file, save_file
    """

    def __init__(self, parent, colors, callbacks, **kwargs):
        super().__init__(parent, fg_color=colors["title_bg"], height=30, corner_radius=0, **kwargs)
        self.colors = colors
        self.callbacks = callbacks
        self.pack_propagate(False)

        # Arrastre de ventana
        self.bind("<ButtonPress-1>", self.callbacks["start_move"])
        self.bind("<B1-Motion>", self.callbacks["do_move"])

        self._create_menus()
        self._create_controls()

    # ------------------------------------------------------------------
    # Menús (File, Edit, …)
    # ------------------------------------------------------------------
    def _create_menus(self):
        menu_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        menu_frame.pack(side=tk.LEFT, padx=5)

        menus = ["File", "Edit", "Selection", "View", "Go", "Run", "Terminal", "Help"]
        for m in menus:
            btn = ctk.CTkLabel(
                menu_frame, text=m, fg_color="transparent",
                text_color=self.colors["menu_fg"], font=("Segoe UI", 12)
            )
            btn.pack(side=tk.LEFT, padx=5)
            btn.bind("<Enter>", lambda e, w=btn: w.configure(fg_color=self.colors["hover"], text_color="#ffffff"))
            btn.bind("<Leave>", lambda e, w=btn: w.configure(fg_color="transparent", text_color=self.colors["menu_fg"]))

            if m == "File":
                self.btn_file = btn
                btn.bind("<Button-1>", lambda e: self._show_file_menu())

    # ------------------------------------------------------------------
    # Controles de ventana (minimizar, maximizar, cerrar)
    # ------------------------------------------------------------------
    def _create_controls(self):
        control_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        control_frame.pack(side=tk.RIGHT)

        ctk.CTkButton(
            control_frame, text="—", fg_color="transparent",
            text_color=self.colors["menu_fg"], hover_color=self.colors["hover"],
            font=("Consolas", 14), width=40, height=30, corner_radius=0,
            command=self.callbacks["minimize"]
        ).pack(side=tk.LEFT)

        self.btn_maximize = ctk.CTkButton(
            control_frame, text="□", fg_color="transparent",
            text_color=self.colors["menu_fg"], hover_color=self.colors["hover"],
            font=("Consolas", 14), width=40, height=30, corner_radius=0,
            command=self.callbacks["maximize"]
        )
        self.btn_maximize.pack(side=tk.LEFT)

        ctk.CTkButton(
            control_frame, text="✕", fg_color="transparent",
            text_color=self.colors["menu_fg"], hover_color="#e81123",
            font=("Consolas", 14), width=40, height=30, corner_radius=0,
            command=self.callbacks["close"]
        ).pack(side=tk.LEFT)

    # ------------------------------------------------------------------
    # Menú contextual de File
    # ------------------------------------------------------------------
    def _show_file_menu(self):
        if hasattr(self, "file_menu") and self.file_menu.winfo_exists():
            self.file_menu.destroy()
            return

        self.file_menu = ctk.CTkToplevel(self)
        self.file_menu.overrideredirect(True)
        self.file_menu.configure(fg_color=self.colors["title_bg"])
        self.file_menu.attributes("-topmost", True)

        options = [
            ("New File",    self.callbacks["new_file"]),
            ("Open File…",  self.callbacks["open_file"]),
            ("Close File",  self.callbacks["close_file"]),
            ("Save",        self.callbacks["save_file"]),
            ("Save As…",    self.callbacks["save_as"]),
            ("Exit",        self.callbacks["close"]),
        ]

        for text, cb in options:
            # Envolver callback para que también cierre el menú
            def _make_cmd(fn):
                def _handler():
                    fn()
                    if hasattr(self, "file_menu") and self.file_menu.winfo_exists():
                        self.file_menu.destroy()
                return _handler

            ctk.CTkButton(
                self.file_menu, text=text, command=_make_cmd(cb),
                fg_color="transparent", anchor="w", corner_radius=0,
                hover_color=self.colors["hover"]
            ).pack(fill="x", padx=2, pady=2)

        x = self.btn_file.winfo_rootx()
        y = self.btn_file.winfo_rooty() + self.btn_file.winfo_height()
        self.file_menu.geometry(f"+{x}+{y}")
        self.file_menu.bind("<FocusOut>", lambda e: self.file_menu.destroy())

        root = self.winfo_toplevel()

        def _reposition(event=None):
            if hasattr(self, "file_menu") and self.file_menu.winfo_exists():
                nx = self.btn_file.winfo_rootx()
                ny = self.btn_file.winfo_rooty() + self.btn_file.winfo_height()
                self.file_menu.geometry(f"+{nx}+{ny}")

        root.bind("<Configure>", _reposition)
        self.file_menu.bind("<Destroy>", lambda e: root.unbind("<Configure>"))

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def update_maximize_icon(self, is_maximized):
        """Actualiza el ícono del botón maximizar/restaurar."""
        self.btn_maximize.configure(text="❐" if is_maximized else "□")
