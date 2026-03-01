import tkinter as tk
import customtkinter as ctk


class QuickAccessBar(ctk.CTkFrame):
    """Barra de acceso rápido con botones de Abrir, Guardar y Compilar.

    callbacks esperados (dict):
        open_file, save_file, run_compile
    """

    def __init__(self, parent, colors, callbacks, **kwargs):
        super().__init__(
            parent,
            fg_color=colors["title_bg"],
            height=36,
            corner_radius=0,
            **kwargs,
        )
        self.colors = colors
        self.callbacks = callbacks
        self.pack_propagate(False)

        self._tooltip = None
        self._build_buttons()

    # ------------------------------------------------------------------
    # Construcción de botones
    # ------------------------------------------------------------------
    def _build_buttons(self):
        btn_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        btn_frame.pack(side=tk.LEFT, padx=6, fill=tk.Y)

        buttons = [
            # (tooltip,          icono unicode,  callback key)
            ("Abrir archivo",    "\uE838",       "open_file"),      # folder / open icon
            ("Guardar archivo",  "\uE74E",       "save_file"),      # save icon
            ("Compilar",         "\uE768",       "run_compile"),    # play icon
            ("Salir",            "\uE711",       "exit_app"),       # close / exit icon
        ]

        for tooltip_text, icon_char, cb_key in buttons:
            btn = ctk.CTkLabel(
                btn_frame,
                text=icon_char,
                fg_color="transparent",
                text_color=self.colors["menu_fg"],
                font=("Segoe MDL2 Assets", 16),
                width=32,
                height=28,
                anchor="center",
            )
            btn.pack(side=tk.LEFT, padx=2, pady=4)

            # Hover
            btn.bind(
                "<Enter>",
                lambda e, w=btn, t=tooltip_text: self._on_enter(w, t),
            )
            btn.bind(
                "<Leave>",
                lambda e, w=btn: self._on_leave(w),
            )
            # Click
            btn.bind(
                "<Button-1>",
                lambda e, k=cb_key: self._fire(k),
            )

        # Separador decorativo (línea vertical sutil)
        sep = ctk.CTkFrame(
            btn_frame, fg_color=self.colors["hover"], width=1, corner_radius=0
        )
        sep.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=6)

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------
    def _fire(self, cb_key):
        cb = self.callbacks.get(cb_key)
        if cb:
            cb()

    def _on_enter(self, widget, tooltip_text):
        widget.configure(
            fg_color=self.colors["hover"], text_color="#ffffff"
        )
        self._show_tooltip(widget, tooltip_text)

    def _on_leave(self, widget):
        widget.configure(
            fg_color="transparent", text_color=self.colors["menu_fg"]
        )
        self._hide_tooltip()

    # ------------------------------------------------------------------
    # Tooltip
    # ------------------------------------------------------------------
    def _show_tooltip(self, widget, text):
        x = widget.winfo_rootx() + widget.winfo_width() // 2
        y = widget.winfo_rooty() + widget.winfo_height() + 4
        self._tooltip = tk.Toplevel(widget)
        self._tooltip.wm_overrideredirect(True)
        self._tooltip.wm_geometry(f"+{x}+{y}")
        ctk.CTkLabel(
            self._tooltip,
            text=text,
            fg_color="#2d2d30",
            text_color="#cccccc",
            font=("Segoe UI", 11),
            corner_radius=4,
        ).pack(padx=4, pady=2)

    def _hide_tooltip(self):
        if self._tooltip:
            self._tooltip.destroy()
            self._tooltip = None
