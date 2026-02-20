from tkinterdnd2 import TkinterDnD
from ui.main_window import DiophantineUI
from utils.preferences import load_preferences

if __name__ == "__main__":
    prefs = load_preferences()
    root = TkinterDnD.Tk()
    app = DiophantineUI(root, prefs=prefs)
    root.mainloop()
