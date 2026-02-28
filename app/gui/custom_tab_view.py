import tkinter as tk
import customtkinter as ctk


class CustomTabView(ctk.CTkFrame):
    """Gestor de pestañas personalizado con botón de cierre por pestaña."""

    def __init__(self, parent, colors, **kwargs):
        super().__init__(parent, **kwargs)
        self.colors = colors

        # Barra de pestañas
        self.tab_bar = ctk.CTkFrame(
            self, height=30, fg_color=self.colors["title_bg"], corner_radius=0
        )
        self.tab_bar.pack(side=tk.TOP, fill=tk.X)
        self.tab_bar.pack_propagate(False)

        # Área de contenido
        self.content_area = ctk.CTkFrame(
            self, fg_color=self.colors["bg"], corner_radius=0
        )
        self.content_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.tabs = {}          # nombre -> (frame_boton, frame_contenido)
        self.current_tab = None
        self.close_callback = None

    def set_close_callback(self, callback):
        """Define la función que se llamará al pulsar la X de una pestaña."""
        self.close_callback = callback

    def add(self, name):
        """Añade una nueva pestaña con el nombre dado."""
        content = ctk.CTkFrame(self.content_area, fg_color=self.colors["bg"], corner_radius=0)

        btn_frame = ctk.CTkFrame(self.tab_bar, fg_color="transparent", corner_radius=0)
        btn_frame.pack(side=tk.LEFT, fill=tk.Y)

        label = ctk.CTkLabel(
            btn_frame, text=name, fg_color="transparent",
            text_color=self.colors["fg"], font=("Segoe UI", 12), padx=10
        )
        label.pack(side=tk.LEFT, fill=tk.Y)
        label.bind("<Button-1>", lambda e, n=name: self.set(n))

        close_btn = ctk.CTkButton(
            btn_frame, text="✕", width=20, height=20,
            fg_color="transparent", hover_color="#e81123",
            text_color=self.colors["fg"], font=("Segoe UI", 10),
            command=lambda n=name: self._close_tab(n)
        )
        close_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.tabs[name] = (btn_frame, content)

        if len(self.tabs) == 1:
            self.set(name)

    def get(self):
        """Devuelve el nombre de la pestaña activa."""
        return self.current_tab

    def set(self, name):
        """Activa la pestaña indicada."""
        if name not in self.tabs:
            return

        if self.current_tab and self.current_tab in self.tabs:
            old_content = self.tabs[self.current_tab][1]
            old_content.pack_forget()
            self._set_tab_style(self.current_tab, selected=False)

        new_content = self.tabs[name][1]
        new_content.pack(fill=tk.BOTH, expand=True)
        self.current_tab = name
        self._set_tab_style(name, selected=True)

    def delete(self, name):
        """Elimina la pestaña y su contenido."""
        if name not in self.tabs:
            return

        btn_frame, content = self.tabs.pop(name)
        btn_frame.destroy()
        content.destroy()

        if self.current_tab == name:
            if self.tabs:
                new_tab = next(iter(self.tabs.keys()))
                self.set(new_tab)
            else:
                self.current_tab = None

    def tab(self, name):
        """Devuelve el frame de contenido de la pestaña indicada."""
        return self.tabs.get(name, (None, None))[1]

    def _close_tab(self, name):
        if self.close_callback:
            self.close_callback(name)
        else:
            self.delete(name)

    def _set_tab_style(self, name, selected):
        if name not in self.tabs:
            return
        btn_frame, _ = self.tabs[name]
        color = self.colors["bg"] if selected else self.colors["title_bg"]
        btn_frame.configure(fg_color=color)
