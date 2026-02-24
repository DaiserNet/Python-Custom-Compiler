import unittest
import tkinter as tk
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.gui.main_window import MainWindow

class TestLayout(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        
    def tearDown(self):
        self.root.update()
        self.root.destroy()
        
    def test_minimum_sizes(self):
        """Verifica que los tamaños mínimos de la ventana sean válidos."""
        app = MainWindow(self.root)
        self.root.update()
        
        # Recupera los tamaños mínimos establecidos en _setup_window
        min_w, min_h = self.root.minsize()
        
        self.assertGreaterEqual(min_w, 400, "El ancho mínimo debe ser al menos 400")
        self.assertGreaterEqual(min_h, 300, "El alto mínimo debe ser al menos 300")

    def test_layout_components_load(self):
        """Verifica la carga correcta del layout y componentes clave (VS Code Fork)."""
        app = MainWindow(self.root)
        self.root.update()
        
        # Validamos la existencia de las barras personalizadas
        self.assertTrue(hasattr(app, 'title_bar'), "La barra de título no está definida")
        self.assertTrue(hasattr(app, 'activity_bar'), "La barra de actividad no está definida")
        self.assertTrue(hasattr(app, 'editor_frame'), "El frame del editor no está definido")
        
        # Verificar que el editor de texto tiene el color de fondo de Dracula Thin
        editor_bg = app.text_editor.cget("bg")
        self.assertEqual(editor_bg, "#282a36", "El fondo del editor debe ser Dracula Thin (#282a36)")
        
        # Verificar cantidad de hijos en la Activity Bar (Mínimo los 3 botones principales)
        activity_children = app.activity_bar.winfo_children()
        self.assertGreaterEqual(len(activity_children), 3, "Deberían haber 3 botones principales en la Activity Bar")

    def test_maximize_symbol_toggle(self):
        """Verifica que el símbolo del botón maximizar cambia entre □ y ❐."""
        app = MainWindow(self.root)
        self.root.update()
        
        # Maximize behavior depends heavily on the OS (especially the ctypes part). 
        # But we can test the internal toggle logic.
        initial_text = app.btn_maximize.cget("text")
        self.assertEqual(initial_text, "□", "El símbolo inicial debe ser el de maximizar")
        
        # Simulamos clic en maximizar
        app._maximize_window()
        self.root.update()
        maximized_text = app.btn_maximize.cget("text")
        self.assertEqual(maximized_text, "❐", "El símbolo post-maximizar debe ser el de restaurar")
        
        # Simulamos clic en restaurar
        app._maximize_window()
        self.root.update()
        restored_text = app.btn_maximize.cget("text")
        self.assertEqual(restored_text, "□", "El símbolo tras restaurar debe volver a ser el de maximizar")

if __name__ == '__main__':
    unittest.main()
