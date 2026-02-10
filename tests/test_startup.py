import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestProjectBase(unittest.TestCase):
    def test_module_loading(self):
        """Verifica que los módulos core y gui se pueden importar."""
        try:
            import app.core.engine
            import app.gui.main_window
            loaded = True
        except ImportError:
            loaded = False
        self.assertTrue(loaded, "Error al cargar los módulos base")

if __name__ == '__main__':
    unittest.main()
