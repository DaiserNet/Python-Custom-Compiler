import tkinter as tk
import customtkinter as ctk


class ActivityBar(ctk.CTkFrame):
    """Barra lateral de actividad con íconos (Explorer, Search, Run & Debug).

    on_panel_switch(panel_name: str) será invocado al hacer clic en un ícono.
    """

    def __init__(self, parent, colors, on_panel_switch=None, **kwargs):
        super().__init__(parent, fg_color=colors["activity_bg"], width=50, corner_radius=0, **kwargs)
        self.colors = colors
        self._on_panel_switch = on_panel_switch
        self.pack_propagate(False)

        self._tooltip = None
        self._build_icons()

    # ------------------------------------------------------------------
    def _build_icons(self):
        activities = [
            ("Explorer",      "\uE8B7",  "explorer"),
            ("Code Search",   "\uE721",  "search"),
            ("Run and Debug", "\uE768",  "run"),
        ]
        for label_text, icon_char, panel_key in activities:
            btn = ctk.CTkLabel(
                self, text=icon_char, fg_color="transparent",
                text_color=self.colors["menu_fg"],
                font=("Segoe MDL2 Assets", 22), width=50, height=50,
            )
            btn.pack(side=tk.TOP, fill=tk.X)
            btn.bind("<Enter>", lambda e, w=btn, t=label_text: self._show_tooltip(w, t))
            btn.bind("<Leave>", lambda e, w=btn: self._hide_tooltip(w))
            btn.bind("<Button-1>", lambda e, k=panel_key: self._fire(k))

    def _fire(self, panel_key):
        if self._on_panel_switch:
            self._on_panel_switch(panel_key)

    # ------------------------------------------------------------------
    # Tooltip
    # ------------------------------------------------------------------
    def _show_tooltip(self, widget, text):
        widget.configure(fg_color=self.colors["hover"], text_color="#ffffff")
        x = widget.winfo_rootx() + 55
        y = widget.winfo_rooty() + 10
        self._tooltip = tk.Toplevel(widget)
        self._tooltip.wm_overrideredirect(True)
        self._tooltip.wm_geometry(f"+{x}+{y}")
        ctk.CTkLabel(
            self._tooltip, text=text, fg_color="#2d2d30", text_color="#cccccc",
            font=("Segoe UI", 12), corner_radius=4
        ).pack(padx=2, pady=2)

    def _hide_tooltip(self, widget):
        widget.configure(fg_color="transparent", text_color=self.colors["menu_fg"])
        if self._tooltip:
            self._tooltip.destroy()
            self._tooltip = None
