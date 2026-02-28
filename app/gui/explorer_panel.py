import os
import tkinter as tk
import customtkinter as ctk


class ExplorerPanel(ctk.CTkFrame):
    """Panel lateral del explorador de archivos.

    on_open_file(file_path, file_name) se invoca al hacer clic en un archivo.
    """

    SKIP_DIRS = {'__pycache__', '.git', 'venv', '.idea', 'node_modules',
                 '.mypy_cache', '.pytest_cache'}

    def __init__(self, parent, colors, on_open_file=None, **kwargs):
        super().__init__(parent, fg_color=colors["activity_bg"], width=250, corner_radius=0, **kwargs)
        self.colors = colors
        self._on_open_file = on_open_file
        self._expanded_folders = set()
        self.pack_propagate(False)

        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    # Construcción de la UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        # Encabezado
        header = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0, height=30)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="EXPLORER", fg_color="transparent",
            text_color=self.colors["menu_fg"], font=("Segoe UI", 11), anchor="w"
        ).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        # Separador
        ctk.CTkFrame(self, fg_color=self.colors["hover"], height=1, corner_radius=0).pack(fill=tk.X)

        # Árbol de archivos (scrollable)
        self.tree = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=self.colors["activity_bg"],
            scrollbar_button_hover_color=self.colors["hover"]
        )
        self.tree.pack(fill=tk.BOTH, expand=True)

    # ------------------------------------------------------------------
    # Renderizado del árbol
    # ------------------------------------------------------------------
    def refresh(self):
        """Reconstruye completamente el árbol de archivos."""
        for w in self.tree.winfo_children():
            w.destroy()

        base_path = os.getcwd()
        folder_name = os.path.basename(base_path)

        root_row = ctk.CTkFrame(self.tree, fg_color="transparent", height=28, corner_radius=0)
        root_row.pack(fill=tk.X)
        root_row.pack_propagate(False)
        ctk.CTkLabel(
            root_row, text=f"\U0001F4C2  {folder_name}",
            fg_color="transparent", text_color=self.colors["strings"],
            font=("Segoe UI", 12, "bold"), anchor="w"
        ).pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8)

        self._render_tree(base_path, 1)

    def _render_tree(self, path, level):
        try:
            entries = os.listdir(path)
        except PermissionError:
            return

        dirs = sorted([e for e in entries if os.path.isdir(os.path.join(path, e))], key=str.lower)
        files = sorted([e for e in entries if not os.path.isdir(os.path.join(path, e))], key=str.lower)

        for entry in dirs + files:
            full_path = os.path.join(path, entry)
            is_dir = os.path.isdir(full_path)

            if is_dir and entry in self.SKIP_DIRS:
                continue

            indent = level * 18

            if is_dir:
                is_expanded = full_path in self._expanded_folders
                icon = "\U0001F4C2" if is_expanded else "\U0001F4C1"
            else:
                icon = "\U0001F4C4"

            row = ctk.CTkFrame(self.tree, fg_color="transparent", height=26, corner_radius=0)
            row.pack(fill=tk.X)
            row.pack_propagate(False)

            label = ctk.CTkLabel(
                row, text=f"{icon}  {entry}", fg_color="transparent",
                text_color=self.colors["fg"], font=("Segoe UI", 12), anchor="w"
            )
            label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(indent + 4, 0))

            for w in (row, label):
                w.bind("<Enter>", lambda e, r=row: r.configure(fg_color=self.colors["hover"]))
                w.bind("<Leave>", lambda e, r=row: r.configure(fg_color="transparent"))

            if is_dir:
                for w in (row, label):
                    w.bind("<Button-1>", lambda e, fp=full_path: self._toggle_folder(fp))
                if is_expanded:
                    self._render_tree(full_path, level + 1)
            else:
                for w in (row, label):
                    w.bind("<Button-1>", lambda e, fp=full_path, fn=entry: self._fire_open(fp, fn))

    # ------------------------------------------------------------------
    # Interacción
    # ------------------------------------------------------------------
    def _toggle_folder(self, folder_path):
        if folder_path in self._expanded_folders:
            to_remove = [p for p in self._expanded_folders if p.startswith(folder_path)]
            for p in to_remove:
                self._expanded_folders.discard(p)
        else:
            self._expanded_folders.add(folder_path)
        self.refresh()

    def _fire_open(self, file_path, file_name):
        if self._on_open_file:
            self._on_open_file(file_path, file_name)
