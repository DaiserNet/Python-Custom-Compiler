import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
import os

from app.gui.custom_tab_view import CustomTabView
from app.gui.title_bar import TitleBar
from app.gui.quick_access_bar import QuickAccessBar
from app.gui.activity_bar import ActivityBar
from app.gui.explorer_panel import ExplorerPanel
from app.gui.search_panel import SearchPanel
from app.gui.run_panel import RunPanel
from app.gui.bottom_panel import BottomPanel
from app.gui.right_panel import RightPanel
from app.gui.components import CodeEditorFrame
from app.gui.status_bar import StatusBar

class MainWindow:
    """Ventana principal – actúa como controlador / orquestador."""
    def __init__(self, root: ctk.CTk):
        self.root = root

        # Estado de archivos / editores
        self.editors = {}
        self.opened_files = {}
        self.untitled_count = 0

        # Configuración base
        self._setup_window()
        self._setup_colors()
        self._create_ui()

        # Editor activo para actualizar status bar
        self.current_editor = None   

    # ==================================================================
    # Colores (Dracula)
    # ==================================================================
    def _setup_colors(self):
        self.colors = {
            "bg":          "#282a36",
            "fg":          "#f8f8f2",
            "title_bg":    "#1e1e1e",
            "activity_bg": "#21222c",
            "menu_fg":     "#cccccc",
            "hover":       "#44475a",
            "comments":    "#6272a4",
            "strings":     "#f1fa8c",
            "keywords":    "#ff79c6",
            "functions":   "#50fa7b",
            "variables":   "#8be9fd",
        }

    # ==================================================================
    # Construcción de la UI
    # ==================================================================
    def _create_ui(self):
        # Contenedor raíz
        self.main_container = ctk.CTkFrame(
            self.root, fg_color="#1e1e1e", border_width=1,
            border_color="#000000", corner_radius=0
        )
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # --- Barra de título ---
        self.title_bar = TitleBar(self.main_container, self.colors, callbacks={
            "start_move": self._start_move,
            "do_move":    self._do_move,
            "minimize":   self._minimize_window,
            "maximize":   self._maximize_window,
            "close":      self.root.destroy,
            "new_file":   self._on_new_file,
            "open_file":  self._on_open_file,
            "close_file": self._on_close_file,
            "save_file":  self._on_save_file,
            "save_as":    self._on_save_as_file,
        })
        self.title_bar.pack(fill=tk.X, side=tk.TOP)

        # --- Barra de acceso rápido ---
        self.quick_access_bar = QuickAccessBar(
            self.main_container, self.colors, callbacks={
                "open_file":   self._on_open_file,
                "save_file":   self._on_save_file,
                "run_compile": self._on_run_compile,
                "exit_app":    self.root.destroy,
            }
        )
        self.quick_access_bar.pack(fill=tk.X, side=tk.TOP)

        # Barra de estado (abajo)
        self.status_bar = StatusBar(self.main_container, self.colors)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # --- Cuerpo ---
        self.body_frame = ctk.CTkFrame(self.main_container, fg_color=self.colors["bg"], corner_radius=0)
        self.body_frame.pack(fill=tk.BOTH, expand=True)

        # Barra de actividad (izquierda)
        self.activity_bar = ActivityBar(
            self.body_frame, self.colors,
            on_panel_switch=self._show_side_panel,
        )
        self.activity_bar.pack(side=tk.LEFT, fill=tk.Y)

        # Paneles laterales izquierda
        self.explorer_panel = ExplorerPanel(
            self.body_frame, self.colors,
            on_open_file=self._open_file_from_explorer,
        )
        self.explorer_panel.pack(side=tk.LEFT, fill=tk.Y)

        self.search_panel = SearchPanel(self.body_frame, self.colors)
        self.search_panel.pack(side=tk.LEFT, fill=tk.Y)

        self.run_panel = RunPanel(
            self.body_frame, self.colors,
            on_run=self._on_run_compile,
        )
        self.run_panel.pack(side=tk.LEFT, fill=tk.Y)

        # Editor central
        self._create_editor_area()

        # Panel derecho
        self.right_panel = RightPanel(self.body_frame, self.colors)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y)

        # Estado inicial: solo explorer visible
        self._active_panel = "explorer"
        self.search_panel.pack_forget()
        self.run_panel.pack_forget()
        self.right_panel.pack_forget()

        

    # ==================================================================
    # Deteccion de Cursor para actualizar Status Bar
    # ==================================================================
    def _on_cursor_move(self, line, col):
        """Callback llamado desde el editor cuando el cursor se mueve."""
        self.status_bar.update_cursor_position(line, col)

    def _update_status_from_editor(self):
        """Actualiza la barra con la posición actual del editor activo."""
        if self.current_editor:
            cursor_index = self.current_editor.text.index(tk.INSERT)
            line, col = cursor_index.split('.')
            line = int(line)
            col = int(col) + 1
            self.status_bar.update_cursor_position(line, col)

    def _on_tab_changed(self, tab_name):
        """Se ejecuta al cambiar de pestaña."""
        if tab_name is None:
            self.current_editor = None
            self.status_bar.update_cursor_position(0, 0)   # O " - "
            self.status_bar.update_file_type("")
        elif tab_name in self.editors:
            self.current_editor = self.editors[tab_name]
            self._update_status_from_editor()
            # Opcional: mostrar extensión del archivo
            ext = os.path.splitext(tab_name)[1] or "Texto"
            self.status_bar.update_file_type(ext)


    # ------------------------------------------------------------------
    # Área del editor + panel inferior
    # ------------------------------------------------------------------
    def _create_editor_area(self):
        self.editor_frame = ctk.CTkFrame(self.body_frame, fg_color=self.colors["bg"], corner_radius=0)
        self.editor_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Tab manager
        self.tab_manager = CustomTabView(self.editor_frame, colors=self.colors)
        self.tab_manager.pack(fill=tk.BOTH, expand=True)
        self.tab_manager.set_close_callback(self._on_tab_close)
        self.tab_manager.on_tab_change = self._on_tab_changed # Vinculamos el callback de cambio de pestaña

        # Panel inferior (oculto por defecto)
        self.bottom_panel = BottomPanel(self.editor_frame, self.colors)

        # Pestaña de bienvenida
        sample_code = (
            "# Archivo principal\n"
            "def mi_funcion():\n"
            '    saludo = "Hola mundo"\n'
            "    print(saludo)\n"
            "    return True\n"
        )
        self._add_new_tab("Welcome.txt", sample_code)

        # Colorear el ejemplo
        editor = self.editors["Welcome.txt"]
        tw = editor.text
        tw.tag_configure("comment",  foreground=self.colors["comments"])
        tw.tag_configure("string",   foreground=self.colors["strings"])
        tw.tag_configure("keyword",  foreground=self.colors["keywords"])
        tw.tag_configure("function", foreground=self.colors["functions"])
        tw.tag_configure("variable", foreground=self.colors["variables"])
        tw.tag_add("comment",  "1.0",  "1.19")
        tw.tag_add("keyword",  "2.0",  "2.3")
        tw.tag_add("function", "2.4",  "2.14")
        tw.tag_add("variable", "3.4",  "3.10")
        tw.tag_add("string",   "3.13", "3.25")
        tw.tag_add("keyword",  "5.4",  "5.10")
        tw.tag_add("variable", "4.10", "4.16")

    def _add_new_tab(self, name, content=""):
        self.tab_manager.add(name)
        tab_frame = self.tab_manager.tab(name)
        editor = CodeEditorFrame(tab_frame, self.colors, on_cursor_move=self._on_cursor_move)
        editor.pack(fill=tk.BOTH, expand=True)
        editor.text.insert("1.0", content)
        self.editors[name] = editor
        editor._on_change()
        self.tab_manager.set(name)
        # Actualizar editor actual y barra de estado
        self.current_editor = editor
        self._update_status_from_editor()

    # ==================================================================
    # Gestión de paneles laterales
    # ==================================================================
    def _show_side_panel(self, panel_name):
        panels = {
            "explorer": self.explorer_panel,
            "search":   self.search_panel,
            "run":      self.run_panel,
        }

        if self._active_panel == panel_name:
            panels[panel_name].pack_forget()
            self._active_panel = None
            return

        if self._active_panel and self._active_panel in panels:
            panels[self._active_panel].pack_forget()

        panels[panel_name].pack(side=tk.LEFT, fill=tk.Y, before=self.editor_frame)
        self._active_panel = panel_name

    # ==================================================================
    # Evento "Ejecutar y Compilar"
    # ==================================================================
    def _on_run_compile(self):
        if self.bottom_panel.visible:
            self.bottom_panel.hide()
            self.right_panel.hide()
        else:
            self.bottom_panel.show(height=150)
            self.right_panel.show()

    # ==================================================================
    # Operaciones de archivo
    # ==================================================================
    def _on_new_file(self):
        self.untitled_count += 1
        name = f"Untitled-{self.untitled_count}.txt"
        self.opened_files[name] = None
        self._add_new_tab(name, "")

    def _on_open_file(self):
        file_path = filedialog.askopenfilename(
            title="Abrir archivo de código",
            filetypes=[("Archivos de texto", "*.txt"), ("Python", "*.py"), ("Todos", "*.*")]
        )
        if not file_path:
            return
        file_name = os.path.basename(file_path)
        content = self._read_file_safe(file_path)
        if content is None:
            return
        self._add_new_tab(file_name, content)
        self.opened_files[file_name] = file_path

    def _on_close_file(self):
        tab_name = self.tab_manager.get()
        if tab_name:
            self._on_tab_close(tab_name)

    def _on_save_file(self):
        tab_name = self.tab_manager.get()
        if not tab_name or tab_name not in self.editors:
            return

        file_path = self.opened_files.get(tab_name)
        if not file_path:
            file_path = filedialog.asksaveasfilename(
                initialfile=tab_name, defaultextension=".txt",
                filetypes=[("Archivos de texto", "*.txt"), ("Todos", "*.*")]
            )
            if not file_path:
                return

        content = self.editors[tab_name].text.get("1.0", tk.END)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.opened_files[tab_name] = file_path
        except Exception as e:
            print(f"Error al guardar: {e}")

    def _on_save_as_file(self):
        tab_name = self.tab_manager.get()
        if not tab_name or tab_name not in self.editors:
            return

        file_path = filedialog.asksaveasfilename(
            initialfile=tab_name, defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos", "*.*")]
        )
        if not file_path:
            return

        content = self.editors[tab_name].text.get("1.0", tk.END)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.opened_files[tab_name] = file_path
        except Exception as e:
            print(f"Error al guardar: {e}")

    def _on_tab_close(self, tab_name):
        if tab_name:
            self.tab_manager.delete(tab_name)
            self.opened_files.pop(tab_name, None)
            self.editors.pop(tab_name, None)

    def _open_file_from_explorer(self, file_path, file_name):
        if file_name in self.opened_files:
            self.tab_manager.set(file_name)
            return
        content = self._read_file_safe(file_path)
        if content is None:
            return
        self._add_new_tab(file_name, content)
        self.opened_files[file_name] = file_path

    @staticmethod
    def _read_file_safe(path):
        """Lee un archivo intentando UTF-8, luego latin-1."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(path, "r", encoding="latin-1") as f:
                    return f.read()
            except Exception:
                return None
        except Exception:
            return None

    # ==================================================================
    # Configuración de la ventana
    # ==================================================================
    def _setup_window(self):
        self.root.geometry("800x600")
        self.root.minsize(400, 300)
        self.root.title("Chimera - VS Code Fork")

        self.root.overrideredirect(True)
        self.root.after(10, self._set_appwindow)
        self._offsetx = 0
        self._offsety = 0
        self._is_maximized = False
        self._normal_geometry = "800x600+100+100"

        self._hover_edge = None
        self._resize_edge = None
        self.root.bind_all("<Motion>", self._check_resize_hover)
        self.root.bind_all("<ButtonPress-1>", self._start_resize)
        self.root.bind_all("<B1-Motion>", self._do_resize)
        self.root.bind_all("<ButtonRelease-1>", self._stop_resize)

    def _set_appwindow(self):
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            GWL_EXSTYLE    = -20
            WS_EX_APPWINDOW = 0x00040000
            WS_EX_TOOLWINDOW = 0x00000080
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style = (style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
            self.root.withdraw()
            self.root.deiconify()
        except Exception as e:
            print(e)

    # ------------------------------------------------------------------
    # Mover / Redimensionar / Minimizar / Maximizar
    # ------------------------------------------------------------------
    def _start_move(self, event):
        if self._hover_edge:
            return
        if self._is_maximized:
            self._maximize_window()
            self.x = event.x
        else:
            self.x = event.x
        self.y = event.y

    def _do_move(self, event):
        if not self._is_maximized:
            self.root.geometry(f"+{event.x_root - self.x}+{event.y_root - self.y}")

    def _minimize_window(self):
        self.root.withdraw()
        self.root.overrideredirect(False)
        self.root.iconify()
        self.root.bind("<Map>", self._restore_window_state)

    def _restore_window_state(self, event):
        self.root.overrideredirect(True)
        self.root.unbind("<Map>")
        self.root.after(10, self._set_appwindow)

    def _maximize_window(self):
        if not self._is_maximized:
            self._normal_geometry = self.root.geometry()
            try:
                import ctypes, struct
                scaling = ctk.get_window_scaling(self.root)
                rect = ctypes.create_string_buffer(16)
                ctypes.windll.user32.SystemParametersInfoA(48, 0, rect, 0)
                left, top, right, bottom = struct.unpack("llll", rect.raw)
                w = int((right - left) / scaling)
                h = int((bottom - top) / scaling)
                self.root.geometry(f"{w}x{h}+{left}+{top}")
            except Exception:
                self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
            self._is_maximized = True
        else:
            self.root.geometry(self._normal_geometry)
            self._is_maximized = False

        self.title_bar.update_maximize_icon(self._is_maximized)

    # ------------------------------------------------------------------
    # Resize por bordes
    # ------------------------------------------------------------------
    def _check_resize_hover(self, event):
        if self._is_maximized or self._resize_edge:
            return
        x = event.x_root - self.root.winfo_rootx()
        y = event.y_root - self.root.winfo_rooty()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        pad = 8
        edge = ""
        if y >= h - pad:    edge += "bottom"
        elif y <= pad:      edge += "top"
        if x >= w - pad:    edge += "right"
        elif x <= pad:      edge += "left"

        cursors = {
            "topleft": "size_nw_se", "bottomright": "size_nw_se",
            "topright": "size_ne_sw", "bottomleft": "size_ne_sw",
            "left": "sb_h_double_arrow", "right": "sb_h_double_arrow",
            "top": "sb_v_double_arrow", "bottom": "sb_v_double_arrow",
        }
        cursor = cursors.get(edge, "")
        self.root.configure(cursor=cursor)
        self._hover_edge = edge or None

    def _start_resize(self, event):
        if self._hover_edge:
            self._resize_edge = self._hover_edge
            self._rs_x = event.x_root
            self._rs_y = event.y_root
            self._rs_w = self.root.winfo_width()
            self._rs_h = self.root.winfo_height()
            self._rs_rx = self.root.winfo_rootx()
            self._rs_ry = self.root.winfo_rooty()

    def _do_resize(self, event):
        if not self._resize_edge:
            return
        dx = event.x_root - self._rs_x
        dy = event.y_root - self._rs_y
        nw, nh = self._rs_w, self._rs_h
        nx, ny = self._rs_rx, self._rs_ry

        if "right" in self._resize_edge:
            nw = max(400, self._rs_w + dx)
        elif "left" in self._resize_edge:
            nw = max(400, self._rs_w - dx)
            nx = self._rs_rx + dx if nw > 400 else self._rs_rx + (self._rs_w - 400)

        if "bottom" in self._resize_edge:
            nh = max(300, self._rs_h + dy)
        elif "top" in self._resize_edge:
            nh = max(300, self._rs_h - dy)
            ny = self._rs_ry + dy if nh > 300 else self._rs_ry + (self._rs_h - 300)

        self.root.geometry(f"{nw}x{nh}+{nx}+{ny}")
        return "break"

    def _stop_resize(self, event):
        self._resize_edge = None
        self._check_resize_hover(event)
