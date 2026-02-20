import tkinter as tk
from tkinter import filedialog, ttk

from utils.preferences import load_preferences, save_preferences


class PreferencesWindow:
    """Preferences dialog for app-wide settings."""

    def __init__(self, app):
        self.app = app

        self.win = tk.Toplevel(app.root)
        self.win.title("Preferences")
        self.win.geometry("450x320")
        self.win.resizable(False, False)
        self.win.transient(app.root)
        self.win.grab_set()

        prefs = load_preferences()
        p = app.palette

        main = ttk.Frame(self.win)
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Default output directory
        ttk.Label(main, text="Default Output Directory",
            font=("", 11, "bold")).pack(anchor=tk.W, pady=(0, 4))

        dir_row = ttk.Frame(main)
        dir_row.pack(fill=tk.X, pady=(0, 12))

        self.output_var = tk.StringVar(value=prefs.get("output_directory", ""))
        tk.Entry(dir_row, textvariable=self.output_var,
            font=("", 11), bg=p["entry_bg"], fg=p["entry_fg"],
            relief=tk.FLAT, highlightbackground=p["highlight_border"],
            highlightthickness=1, insertbackground=p["insert_bg"]
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(dir_row, text="Browse",
            command=self._browse_dir
        ).pack(side=tk.RIGHT, padx=(5, 0))

        # Default encryption method
        ttk.Label(main, text="Default Encryption Method",
            font=("", 11, "bold")).pack(anchor=tk.W, pady=(0, 4))

        self.method_var = tk.StringVar(
            value=prefs.get("encryption_method", "zip"))
        ttk.Combobox(main, textvariable=self.method_var,
            values=["zip", "7z", "veracrypt", "gpg"],
            state='readonly', width=20, font=("", 10)
        ).pack(anchor=tk.W, pady=(0, 12))

        # Default naming scheme
        ttk.Label(main, text="Default Naming Scheme",
            font=("", 11, "bold")).pack(anchor=tk.W, pady=(0, 4))

        self.naming_var = tk.StringVar(
            value=prefs.get("naming_scheme", "original"))
        ttk.Combobox(main, textvariable=self.naming_var,
            values=["original", "numeric", "chronos"],
            state='readonly', width=20, font=("", 10)
        ).pack(anchor=tk.W, pady=(0, 12))

        # Buttons
        btn_row = ttk.Frame(main)
        btn_row.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(btn_row, text="Save",
            command=self._save, default="active"
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(btn_row, text="Cancel",
            command=self.win.destroy
        ).pack(side=tk.RIGHT)

    def _browse_dir(self):
        directory = filedialog.askdirectory(title="Select default output directory")
        if directory:
            self.output_var.set(directory)

    def _save(self):
        prefs = {
            "output_directory": self.output_var.get(),
            "encryption_method": self.method_var.get(),
            "naming_scheme": self.naming_var.get(),
        }
        save_preferences(prefs)
        self.app.apply_preferences(prefs)
        self.win.destroy()
