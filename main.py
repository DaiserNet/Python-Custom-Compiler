import tkinter as tk
from app.gui.main_window import MainWindow

def main():
    root = tk.Tk()
    root.title("Chimera")
    
    # Inicialización de la UI
    app = MainWindow(root)
    
    print("Ejecutando IDE")
    root.mainloop()

if __name__ == "__main__":
    main()
