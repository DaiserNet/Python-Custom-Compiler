import tkinter as tk
import customtkinter as ctk
from app.gui.main_window import MainWindow

def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue") 
    
    ctk.set_widget_scaling(1.0) 
    ctk.set_window_scaling(1.0)

    root = ctk.CTk()
    root.title("Chimera")
    
    app = MainWindow(root)
    root.mainloop()
    # root = tk.Tk()
    # root.title("Chimera")
    
    # # Inicialización de la UI
    # app = MainWindow(root)
    
    # print("Ejecutando IDE")
    # root.mainloop()

if __name__ == "__main__":
    main()
