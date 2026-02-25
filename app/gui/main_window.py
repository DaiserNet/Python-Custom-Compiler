import tkinter as tk
from tkinter import filedialog # Ventana estándar para elegir archivos
import customtkinter as ctk
import os

class MainWindow:
    def __init__(self, root: ctk.CTk):
        self.root = root

        self.editors = {} # Para almacenar referencias a los editores de cada pestaña
        # Logica de apertura de archivos
        self.opened_files = {}
        self.untitled_count = 0 # Contador para archivos nuevos

        # Creacion de interfaz
        self._setup_window()
        self._setup_colors()
        self._create_widgets()
    
    # Función para abrir archivos, con manejo de múltiples pestañas y prevención de duplicados
    def open_file(self):
        # Seleccion de archivos
        file_path = filedialog.askopenfilename(filetypes=[("Arvhivos de texto", "*.txt"), ("Todos los archivos", "*.*")])
        if file_path:
            file_name = os.path.basename(file_path)

            # Leer contenido
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Guardar en nuestro registro y crear pestaña
            self.opened_files[file_name] = file_path
            self._create_new_tab(file_name, content)

    def _on_open_file(self):
        file_path = filedialog.askopenfilename(
            title="Abrir archivo de código",
            filetypes=[("Archivos de texto", "*.txt"), ("Python", "*.py"), ("Todos", "*.*")]
        )
        
        if file_path:
            file_name = os.path.basename(file_path)
            try:
                # Intentamos leer con UTF-8 (el estándar)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                # PLAN B: Si falla, intentamos con 'latin-1', que lee casi cualquier byte
                try:
                    with open(file_path, "r", encoding="latin-1") as f:
                        content = f.read()
                except Exception as e:
                    print(f"Error fatal al leer: {e}")
                    return

            # Si llegamos aquí, la lectura fue exitosa
            self._add_new_tab(file_name, content)
            # Guardamos la ruta en nuestro diccionario para el futuro "Save"
            self.opened_files[file_name] = file_path

    def _on_new_file(self):
        self.untitled_count += 1
        new_name = f"Untitled-{self.untitled_count}.txt"
        
        # Agregamos al registro de archivos abiertos
        self.opened_files[new_name] = None # None porque aún no tiene ruta en disco
        
        # Creamos la pestaña
        self._add_new_tab(new_name, "")
        
        # Cerramos el menú
        if hasattr(self, "file_menu") and self.file_menu.winfo_exists():
            self.file_menu.destroy()
    
    def _on_close_file(self):
        tab_name = self.tab_manager.get()
        
        if tab_name:
            self.tab_manager.delete(tab_name)
            
            if tab_name in self.opened_files:
                del self.opened_files[tab_name]

        if hasattr(self, "file_menu") and self.file_menu.winfo_exists():
            self.file_menu.destroy()
        
        if tab_name in self.editors:
            del self.editors[tab_name]
    
    # EN main_window.py
    def _on_save_file(self):
        tab_name = self.tab_manager.get() # Nombre de la pestaña actual
        if not tab_name or tab_name not in self.editors:
            return

        # 1. Obtener la ruta (si es nueva, preguntar)
        file_path = self.opened_files.get(tab_name)
        
        if not file_path: # Es un archivo "Untitled"
            file_path = filedialog.asksaveasfilename(
                initialfile=tab_name,
                defaultextension=".txt",
                filetypes=[("Archivos de texto", "*.txt"), ("Todos", "*.*")]
            )
            if not file_path: return # El usuario canceló
            
        # 2. Obtener el texto del editor correspondiente a esa pestaña
        editor_widget = self.editors[tab_name].text
        content = editor_widget.get("1.0", tk.END)

        # 3. Escribir al disco
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.opened_files[tab_name] = file_path # Actualizar registro
            print(f"Guardado exitoso: {file_path}")
        except Exception as e:
            print(f"Error al guardar: {e}")

        if hasattr(self, "file_menu") and self.file_menu.winfo_exists():
            self.file_menu.destroy()

    def _setup_window(self):
        self.root.geometry("800x600")
        self.root.minsize(400, 300)
        self.root.title("Chimera - VS Code Fork")
        
        # Ocultamos la barra por defecto del SO
        self.root.overrideredirect(True)
        self.root.after(10, self._set_appwindow)
        self._offsetx = 0
        self._offsety = 0
        self._is_maximized = False
        self._normal_geometry = "800x600+100+100"
        
        # Variables de estado para resizing por software
        self._hover_edge = None
        self._resize_edge = None
        self.root.bind_all("<Motion>", self._check_resize_hover)
        self.root.bind_all("<ButtonPress-1>", self._start_resize)
        self.root.bind_all("<B1-Motion>", self._do_resize)
        self.root.bind_all("<ButtonRelease-1>", self._stop_resize)

    def _set_appwindow(self):
        # Mantiene el icono en la barra de tareas
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            
            GWL_EXSTYLE = -20
            WS_EX_APPWINDOW = 0x00040000
            WS_EX_TOOLWINDOW = 0x00000080
            
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style = style & ~WS_EX_TOOLWINDOW
            style = style | WS_EX_APPWINDOW
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

            self.root.withdraw()
            self.root.deiconify()
        except Exception as e:
            print(e)

    def _setup_colors(self):
        # Dracula Thin
        self.colors = {
            "bg": "#282a36",
            "fg": "#f8f8f2",
            "title_bg": "#1e1e1e",
            "activity_bg": "#21222c",
            "menu_fg": "#cccccc",
            "hover": "#44475a",
            "comments": "#6272a4",
            "strings": "#f1fa8c",
            "keywords": "#ff79c6",
            "functions": "#50fa7b",
            "variables": "#8be9fd"
        }

    def _create_widgets(self):
        self.main_container = ctk.CTkFrame(self.root, fg_color="#1e1e1e", border_width=1, border_color="#000000", corner_radius=0)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self._create_title_bar()
        self._create_body()

    def _create_title_bar(self):
        self.title_bar = ctk.CTkFrame(self.main_container, fg_color=self.colors["title_bg"], height=30, corner_radius=0)
        self.title_bar.pack(fill=tk.X, side=tk.TOP)
        self.title_bar.pack_propagate(False)

        # Arrastre de ventana
        self.title_bar.bind("<ButtonPress-1>", self._start_move)
        self.title_bar.bind("<B1-Motion>", self._do_move)

        # Menús
        menu_frame = ctk.CTkFrame(self.title_bar, fg_color="transparent", corner_radius=0)
        menu_frame.pack(side=tk.LEFT, padx=5)

        menus = ["File", "Edit", "Selection", "View", "Go", "Run", "Terminal", "Help"]
        for m in menus:
            btn = ctk.CTkLabel(menu_frame, text=m, fg_color="transparent", text_color=self.colors["menu_fg"], font=("Segoe UI", 12))
            btn.pack(side=tk.LEFT, padx=5)
            btn.bind("<Enter>", lambda e, w=btn: w.configure(fg_color=self.colors["hover"], text_color="#ffffff"))
            btn.bind("<Leave>", lambda e, w=btn: w.configure(fg_color="transparent", text_color=self.colors["menu_fg"]))

            # Se utiliza una funcion lambda para que al hacer click en "File" se abra el dialogo de archivos
            if m == "File":
                self.btn_file = btn  # Guardamos referencia para posicionar el menú
                btn.bind("<Button-1>", lambda e, menu=m: self._show_file_menu())

        # Controles ventana
        control_frame = ctk.CTkFrame(self.title_bar, fg_color="transparent", corner_radius=0)
        control_frame.pack(side=tk.RIGHT)

        btn_minimize = ctk.CTkButton(control_frame, text="—", fg_color="transparent", text_color=self.colors["menu_fg"], 
                                     hover_color=self.colors["hover"], font=("Consolas", 14), width=40, height=30, 
                                     corner_radius=0, command=self._minimize_window)
        btn_minimize.pack(side=tk.LEFT)
        
        self.btn_maximize = ctk.CTkButton(control_frame, text="□", fg_color="transparent", text_color=self.colors["menu_fg"], 
                                          hover_color=self.colors["hover"], font=("Consolas", 14), width=40, height=30, 
                                          corner_radius=0, command=self._maximize_window)
        self.btn_maximize.pack(side=tk.LEFT)
        
        btn_close = ctk.CTkButton(control_frame, text="✕", fg_color="transparent", text_color=self.colors["menu_fg"], 
                                  hover_color="#e81123", font=("Consolas", 14), width=40, height=30, 
                                  corner_radius=0, command=self.root.destroy)
        btn_close.pack(side=tk.LEFT)

    def _create_body(self):
        self.body_frame = ctk.CTkFrame(self.main_container, fg_color=self.colors["bg"], corner_radius=0)
        self.body_frame.pack(fill=tk.BOTH, expand=True)

        self._create_activity_bar()
        self._create_editor()

    def _create_activity_bar(self):
        self.activity_bar = ctk.CTkFrame(self.body_frame, fg_color=self.colors["activity_bg"], width=50, corner_radius=0)
        self.activity_bar.pack(side=tk.LEFT, fill=tk.Y)
        self.activity_bar.pack_propagate(False)

        activities = [("Explorer", "E"), ("Code Search", "S"), ("Run and Debug", "D")]
        for fullname, shortname in activities:
            btn = ctk.CTkLabel(self.activity_bar, text=shortname, fg_color="transparent", text_color=self.colors["menu_fg"], 
                               font=("Segoe UI", 16, "bold"), pady=15)
            btn.pack(side=tk.TOP, fill=tk.X)
            btn.bind("<Enter>", lambda e, w=btn, txt=fullname: self._show_tooltip(w, txt))
            btn.bind("<Leave>", lambda e, w=btn: self._hide_tooltip(w))

    def _show_tooltip(self, widget, text):
        widget.configure(text_color="#ffffff")
        x = widget.winfo_rootx() + 55
        y = widget.winfo_rooty() + 10
        self.tooltip = tk.Toplevel(widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = ctk.CTkLabel(self.tooltip, text=text, fg_color="#2d2d30", text_color="#cccccc", 
                             font=("Segoe UI", 12), corner_radius=4)
        label.pack(padx=2, pady=2)

    def _hide_tooltip(self, widget):
        widget.configure(text_color=self.colors["menu_fg"])
        if hasattr(self, "tooltip") and self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    def _create_editor(self):
        self.editor_frame = ctk.CTkFrame(self.body_frame, fg_color=self.colors["bg"], corner_radius=0)
        self.editor_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Implementacion de Tabview para sistema de ventanas
        # anchor="nw" para alinear a la izquierda y evitar centrado
        # self.tab_manager = ctk.CTkTabview(self.editor_frame, corner_radius=0, anchor="nw")
        self.tab_manager = ctk.CTkTabview(
            self.editor_frame, 
            corner_radius=0, 
            anchor="nw",
            fg_color=self.colors["bg"],           # Fondo del contenido
            segmented_button_fg_color="#1e1e1e",  # Fondo de la barra de pestañas
            segmented_button_selected_color=self.colors["bg"], # Color pestaña activa
            segmented_button_selected_hover_color=self.colors["hover"],
            segmented_button_unselected_color="#1e1e1e",
            segmented_button_unselected_hover_color=self.colors["hover"],
            text_color="#f8f8f2"                  # Texto Dracula (blanco hueso)
        )
        self.tab_manager.pack(fill=tk.BOTH, expand=True)

        self.tab_manager._segmented_button.configure(
            selected_color="#bd93f9", # Morado Dracula para la pestaña activa
            unselected_color="#1e1e1e"
        )
        # Creacion de pestaña inicial por defecto
        sample_code = "# Archivo de bienvenida\ndef hello():\n    print('Chimera IDE')\n"
        self._add_new_tab("Welcome.txt", sample_code)
        
        # from app.gui.components import CodeEditorFrame
        # self._code_editor_frame = CodeEditorFrame(self.editor_frame, self.colors)
        # self._code_editor_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        # self.text_editor = self._code_editor_frame.text
        
        # sample_code = (
        #     "# Archivo principal\n"
        #     "def mi_funcion():\n"
        #     "    saludo = \"Hola mundo\"\n"
        #     "    print(saludo)\n"
        #     "    return True\n"
        # )
        # self.text_editor.insert(tk.END, sample_code)
        
        # # Tema demo (Visual solamente para cumplir requerimiento)
        # self.text_editor.tag_configure("comment", foreground=self.colors["comments"])
        # self.text_editor.tag_configure("string", foreground=self.colors["strings"])
        # self.text_editor.tag_configure("keyword", foreground=self.colors["keywords"])
        # self.text_editor.tag_configure("function", foreground=self.colors["functions"])
        # self.text_editor.tag_configure("variable", foreground=self.colors["variables"])

        # self.text_editor.tag_add("comment", "1.0", "1.19")
        # self.text_editor.tag_add("keyword", "2.0", "2.3")
        # self.text_editor.tag_add("keyword", "5.4", "5.10")
        # self.text_editor.tag_add("function", "2.4", "2.14")
        # self.text_editor.tag_add("function", "4.4", "4.9")
        # self.text_editor.tag_add("variable", "3.4", "3.10")
        # self.text_editor.tag_add("variable", "4.10", "4.16")
        # self.text_editor.tag_add("string", "3.13", "3.25")
        
        # self.text_editor.focus_set()

    def _add_new_tab(self, name, content=""):
        # añadir la pestaña al gestor
        self.tab_manager.add(name)

        # obtener el frame de la pestaña recién creada
        tab_frame = self.tab_manager.tab(name)

        # Se mete el editor de código dentro de la pestaña
        from app.gui.components import CodeEditorFrame
        editor = CodeEditorFrame(tab_frame, self.colors)
        editor.pack(fill=tk.BOTH, expand=True)

        # Insertar el contenido inicial
        editor.text.insert("1.0", content)
        self.editors[name] = editor  # Guardamos referencia al editor de esta pestaña
        editor._on_change()  # Forzar actualización de números de línea
        self.tab_manager.set(name)  # Cambiar a la pestaña recién creada

    def _show_file_menu(self):
        # SEGURIDAD: Si el menú ya existe, lo cerramos antes de crear otro
        if hasattr(self, "file_menu") and self.file_menu.winfo_exists():
            self.file_menu.destroy()
            return # Si haces clic de nuevo, simplemente se cierra

        self.file_menu = ctk.CTkToplevel(self.root)
        self.file_menu.overrideredirect(True)
        self.file_menu.configure(fg_color=self.colors["title_bg"])
        
        # Forzar que el menú esté por encima de todo
        self.file_menu.attributes("-topmost", True)

        options = [
            ("New File", self._on_new_file),
            ("Open File...", self._on_open_file),
            ("Close File", self._on_close_file),
            ("Save", lambda: self._on_save_file()) 
        ]

        for text, command in options:
            btn = ctk.CTkButton(
                self.file_menu, text=text, command=command,
                fg_color="transparent", anchor="w", corner_radius=0,
                hover_color=self.colors["hover"]
            )
            btn.pack(fill="x", padx=2, pady=2)

        # Reposicionamiento inicial
        x = self.btn_file.winfo_rootx()
        y = self.btn_file.winfo_rooty() + self.btn_file.winfo_height()
        self.file_menu.geometry(f"+{x}+{y}")

        # Cerrar si se pierde el foco
        self.file_menu.bind("<FocusOut>", lambda e: self.file_menu.destroy())

        # Creamos una función interna para reposicionar
        def reposition(event=None):
            if hasattr(self, "file_menu") and self.file_menu.winfo_exists():
                # Calculamos la nueva posición base del botón "File"
                # Necesitamos obtener la referencia al botón que disparó el menú
                x = self.btn_file.winfo_rootx()
                y = self.btn_file.winfo_rooty() + self.btn_file.winfo_height()
                self.file_menu.geometry(f"+{x}+{y}")

        # Vinculamos el movimiento de la ventana principal al reposicionamiento
        self.root.bind("<Configure>", reposition)
        
        # Es vital limpiar este vínculo cuando el menú se cierre
        self.file_menu.bind("<Destroy>", lambda e: self.root.unbind("<Configure>"))

    # -----------------------------------------------------------------
    # LÓGICA DE VENTANA (Mover, redimensionar, maximizar, minimizar)
    # -----------------------------------------------------------------

    def _check_resize_hover(self, event):
        if self._is_maximized or self._resize_edge:
            return

        x = event.x_root - self.root.winfo_rootx()
        y = event.y_root - self.root.winfo_rooty()
        w = self.root.winfo_width()
        h = self.root.winfo_height()

        padding = 8
        edge = ""
        if y >= h - padding: edge += "bottom"
        elif y <= padding: edge += "top"

        if x >= w - padding: edge += "right"
        elif x <= padding: edge += "left"

        cursor = ""
        if edge in ("topleft", "bottomright"): cursor = "size_nw_se"
        elif edge in ("topright", "bottomleft"): cursor = "size_ne_sw"
        elif edge in ("left", "right"): cursor = "sb_h_double_arrow"
        elif edge in ("top", "bottom"): cursor = "sb_v_double_arrow"

        if cursor:
            self.root.configure(cursor=cursor)
            self._hover_edge = edge
        else:
            self.root.configure(cursor="")
            self._hover_edge = None

    def _start_resize(self, event):
        if self._hover_edge:
            self._resize_edge = self._hover_edge
            self._resize_start_x = event.x_root
            self._resize_start_y = event.y_root
            self._resize_start_w = self.root.winfo_width()
            self._resize_start_h = self.root.winfo_height()
            self._resize_start_rx = self.root.winfo_rootx()
            self._resize_start_ry = self.root.winfo_rooty()

    def _do_resize(self, event):
        if self._resize_edge:
            dx = event.x_root - self._resize_start_x
            dy = event.y_root - self._resize_start_y
            
            new_w = self._resize_start_w
            new_h = self._resize_start_h
            new_x = self._resize_start_rx
            new_y = self._resize_start_ry

            if "right" in self._resize_edge:
                new_w = max(400, self._resize_start_w + dx)
            elif "left" in self._resize_edge:
                new_w = max(400, self._resize_start_w - dx)
                if new_w > 400: new_x = self._resize_start_rx + dx
                else: new_x = self._resize_start_rx + (self._resize_start_w - 400)

            if "bottom" in self._resize_edge:
                new_h = max(300, self._resize_start_h + dy)
            elif "top" in self._resize_edge:
                new_h = max(300, self._resize_start_h - dy)
                if new_h > 300: new_y = self._resize_start_ry + dy
                else: new_y = self._resize_start_ry + (self._resize_start_h - 300)

            self.root.geometry(f"{new_w}x{new_h}+{new_x}+{new_y}")
            return "break"

    def _stop_resize(self, event):
        self._resize_edge = None
        self._check_resize_hover(event)

    def _start_move(self, event):
        if self._hover_edge: return
        if self._is_maximized:
            self._maximize_window()
            self.x = event.x
        else:
            self.x = event.x
            
        self.y = event.y

    def _do_move(self, event):
        if not self._is_maximized:
            deltax = event.x_root - self.x
            deltay = event.y_root - self.y
            self.root.geometry(f"+{deltax}+{deltay}")

    def _minimize_window(self):
        self.root.withdraw() # Ocultar completamente primero
        self.root.overrideredirect(False) # Devolver control al SO
        self.root.iconify() # Minimizar
        self.root.bind("<Map>", self._restore_window_state) # Detectar cuando regresa

    def _restore_window_state(self, event):
        self.root.overrideredirect(True)
        self.root.unbind("<Map>")
        self.root.after(10, self._set_appwindow)

    def _get_work_area(self):
        import ctypes
        import struct
        rect = ctypes.create_string_buffer(16)
        ctypes.windll.user32.SystemParametersInfoA(48, 0, rect, 0)
        left, top, right, bottom = struct.unpack("llll", rect.raw)
        return left, top, right, bottom

    def _maximize_window(self):
        if not self._is_maximized:
            self._normal_geometry = self.root.geometry()
            
            try:
                scaling = ctk.get_window_scaling(self.root)
                left, top, right, bottom = self._get_work_area()
                width = int((right - left) / scaling)
                height = int((bottom - top) / scaling)
                self.root.geometry(f"{width}x{height}+{left}+{top}")
            except Exception:
                w = self.root.winfo_screenwidth()
                h = self.root.winfo_screenheight()
                self.root.geometry(f"{w}x{h}+0+0")
                
            self.btn_maximize.configure(text="❐") # Actualizado a .configure() para CTk
            self._is_maximized = True
        else:
            self.root.geometry(self._normal_geometry)
            self.btn_maximize.configure(text="□") # Actualizado a .configure() para CTk
            self._is_maximized = False