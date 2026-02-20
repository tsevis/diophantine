import tkinter as tk
from tkinter import ttk
import platform

from ui.theme import get_palette, is_macos


class DiophantineUI:
    """Main application shell with tabbed interface."""

    def __init__(self, root, prefs=None):
        self.root = root
        self.root.title("Diophantine")
        self.root.geometry("920x700")
        self.root.minsize(780, 580)

        self.prefs = prefs or {}
        self.palette = get_palette(self.prefs.get("theme"))

        self.style = ttk.Style()
        if is_macos():
            self.style.theme_use("aqua")
        else:
            self.style.theme_use("clam")

        # Track current appearance mode
        self._appearance = "auto"

        self.build()

    def build(self):
        main = ttk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True)

        # ── Top Bar ──────────────────────────────────────────────
        top_bar = ttk.Frame(main)
        top_bar.pack(fill=tk.X, side=tk.TOP)

        title_block = ttk.Frame(top_bar)
        title_block.pack(side=tk.LEFT, padx=(20, 0), pady=(10, 8))

        ttk.Label(title_block, text="Diophantine",
            font=("", 16, "bold")
        ).pack(anchor=tk.W)

        ttk.Label(title_block,
            text="Encryption & compression companion — inspired by Diophantus of Alexandria",
            font=("", 9)
        ).pack(anchor=tk.W)

        ttk.Button(top_bar, text="Preferences",
            command=self.open_preferences
        ).pack(side=tk.RIGHT, padx=(0, 20), pady=12)

        if is_macos():
            self._appearance_btn = ttk.Button(top_bar,
                text="Dark Mode",
                command=self.toggle_appearance)
            self._appearance_btn.pack(side=tk.RIGHT, padx=(0, 5), pady=12)

        ttk.Separator(main, orient="horizontal").pack(fill=tk.X)

        # ── Bottom Bar (shared progress) ─────────────────────────
        bottom_bar = ttk.Frame(main)
        bottom_bar.pack(fill=tk.X, side=tk.BOTTOM)

        ttk.Separator(main, orient="horizontal").pack(
            fill=tk.X, side=tk.BOTTOM)

        progress_row = ttk.Frame(bottom_bar)
        progress_row.pack(fill=tk.X, padx=20, pady=8)

        ttk.Label(progress_row, text="Progress",
            font=("", 10)).pack(side=tk.LEFT, padx=(0, 10))

        self.progress = ttk.Progressbar(progress_row,
            length=200, mode='determinate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # ── Notebook ─────────────────────────────────────────────
        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        from ui.encrypt_tab import EncryptTab
        from ui.decrypt_tab import DecryptTab

        self.encrypt_tab = EncryptTab(self.notebook, self)
        self.decrypt_tab = DecryptTab(self.notebook, self)

        self.notebook.add(self.encrypt_tab.frame, text="  Encrypt  ")
        self.notebook.add(self.decrypt_tab.frame, text="  Decrypt  ")

    # ── Appearance Toggle ────────────────────────────────────────

    def toggle_appearance(self):
        """Toggle between light and dark mode on macOS."""
        try:
            if self._appearance in ("auto", "aqua"):
                self.root.tk.call(
                    '::tk::unsupported::MacWindowStyle',
                    'appearance', '.', 'darkaqua')
                self._appearance = "darkaqua"
                self._appearance_btn.config(text="Light Mode")
            else:
                self.root.tk.call(
                    '::tk::unsupported::MacWindowStyle',
                    'appearance', '.', 'aqua')
                self._appearance = "aqua"
                self._appearance_btn.config(text="Dark Mode")
        except tk.TclError:
            pass

    def open_preferences(self):
        from ui.preferences_window import PreferencesWindow
        PreferencesWindow(self)

    def apply_preferences(self, prefs):
        """Called after preferences are saved."""
        self.prefs = prefs
        self.palette = get_palette(prefs.get("theme"))

    # ── Shared Widget Helpers ────────────────────────────────────

    def checkbox(self, parent, text, variable, command=None):
        if is_macos():
            # ttk.Checkbutton renders natively on aqua and properly
            # inherits the parent background in both light and dark mode.
            cb = ttk.Checkbutton(parent, text=text, variable=variable,
                command=command)
        else:
            p = self.palette
            cb = tk.Checkbutton(parent, text=text, variable=variable,
                font=("", 11), fg=p["entry_fg"],
                selectcolor=p["check_select"],
                relief=tk.FLAT, bd=0, highlightthickness=0, padx=0,
                command=command)
        cb.pack(anchor=tk.W, pady=2)
        return cb

    def radio(self, parent, text, variable, value, command=None):
        if is_macos():
            # ttk.Radiobutton renders natively on aqua.
            rb = ttk.Radiobutton(parent, text=text, variable=variable,
                value=value, command=command)
        else:
            p = self.palette
            rb = tk.Radiobutton(parent, text=text, variable=variable,
                value=value, font=("", 11), fg=p["entry_fg"],
                selectcolor=p["check_select"],
                relief=tk.FLAT, bd=0, highlightthickness=0, padx=0,
                command=command)
        rb.pack(anchor=tk.W, pady=1)
        return rb

    @staticmethod
    def section_label(parent, text):
        ttk.Label(parent, text=text,
            font=("", 10, "bold")
        ).pack(anchor=tk.W, pady=(10, 3))
