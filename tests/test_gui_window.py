import unittest
import tkinter as tk
import sys
import os

# Asegurar que el path incluya la raíz del proyecto para importar 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.gui.main_window import MainWindow

class TestMainWindow(unittest.TestCase):
    def setUp(self):
        """Prepara el entorno creando la raíz de Tkinter para cada test."""
        self.root = tk.Tk()
        
    def tearDown(self):
        """Limpia el entorno destruyendo la raíz de Tkinter tras cada test."""
        # Se asegura de actualizar y luego destruir para evitar errores de Tcl persistentes
        self.root.update()
        self.root.destroy()
        
    def test_create_and_close_window(self):
        """Verifica que la ventana principal se crea y puede contener sus widgets sin excepciones."""
        exception_raised = False
        try:
            # Intentar instanciar la ventana
            app = MainWindow(self.root)
            
            # Verificar propiedades iniciales (p.ej. que el editor exista)
            self.assertIsNotNone(app.text_editor)
            
            # Dar un ciclo de actualización para que Tkinter procese los widgets
            self.root.update()
            
        except Exception as e:
            exception_raised = True
            print(f"Excepción al crear la ventana: {e}")
            
        self.assertFalse(exception_raised, "Se lanzó una excepción al crear o configurar la ventana principal.")

    def test_text_insertion(self):
        app = MainWindow(self.root)        
        # Insertar texto de prueba
        test_text = "Línea 1\nLínea 2\nLínea 3 con más contenido."
        app.text_editor.insert(tk.END, test_text)
        
        # El texto se inserta, forzamos una actualización
        self.root.update()
        
        # Extraer el texto actual del widget (Tkinter agrega un \n al final automáticamente)
        content = app.text_editor.get("1.0", tk.END)
        
        self.assertTrue(test_text in content, "El texto insertado no se encontró completo en el editor.")

    def test_read_content(self):
        app = MainWindow(self.root)
        test_text = "Prueba de lectura"
        
        app.text_editor.insert(tk.END, test_text)
        self.root.update()
        
        # Leer desde la primera línea, primer caracter hasta el final (quitando el salto de línea extra de Tkinter con strip)
        read_text = app.text_editor.get("1.0", tk.END).strip()
        
        self.assertEqual(read_text, test_text, "El contenido leído no coincide con el insertado.")


if __name__ == '__main__':
    unittest.main()
