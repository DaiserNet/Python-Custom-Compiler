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
        # CTkFrame usa fg_color
        super().__init__(parent, fg_color=colors["bg"], corner_radius=0, *args, **kwargs)
        self.colors = colors

        self.linenumbers = LineNumberCanvas(self, None, colors, width=40)
        self.linenumbers.pack(side=tk.LEFT, fill=tk.Y)

        self.text = CustomText(
            self,
            bg=self.colors["bg"], 
            fg=self.colors["variables"], 
            insertbackground=self.colors["fg"], 
            wrap=tk.WORD, 
            font=("Consolas", 12),
            bd=0,
            highlightthickness=0
        )
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.linenumbers.text_widget = self.text

        # Reemplazamos tk.Scrollbar por el moderno CTkScrollbar
        self.scrollbar = ctk.CTkScrollbar(self, orientation="vertical", command=self.text.yview)
        
        def _on_yscroll(*args):
            self.scrollbar.set(*args)
            self._on_change()
            
        self.text.configure(yscrollcommand=_on_yscroll)
        # Puedes empaquetar la scrollbar ahora, se verá genial con el estilo oscuro
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y) 

        self.text.bind("<<Change>>", self._on_change)
        self.text.bind("<Configure>", self._on_change)
        self.text.bind("<KeyRelease>", self._on_change)
        self.text.bind("<ButtonRelease-1>", self._on_change)
        self.text.bind("<MouseWheel>", self._on_change)

    def _on_change(self, event=None):
        self.linenumbers.redraw()