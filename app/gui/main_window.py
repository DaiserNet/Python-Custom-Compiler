import tkinter as tk

class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self._setup_window()
        self._create_widgets()

    def _setup_window(self):
        self.root.geometry("800x600")
        self.root.minsize(400, 300)

    def _create_widgets(self):
        # Frame principal
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Área de texto
        self.text_editor = tk.Text(main_frame, wrap=tk.WORD, font=("Consolas", 12))
        self.text_editor.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar para el área de texto
        scrollbar = tk.Scrollbar(self.text_editor)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_editor.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.text_editor.yview)

        # Foco inicial en el editor
        self.text_editor.focus_set()
