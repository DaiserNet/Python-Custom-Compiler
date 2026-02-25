import tkinter as tk
import customtkinter as ctk

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
    def __init__(self, parent, colors, *args, **kwargs):
        super().__init__(parent, fg_color=colors["bg"], corner_radius=0, *args, **kwargs)
        self.colors = colors

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
        self.text.bind("<MouseWheel>", self._on_change)

    def _on_change(self, event=None):
        self.text.update_idletasks()
        self.linenumbers.redraw()