import tkinter as tk
from tkinter import ttk
import secrets
import string


class PasswordGeneratorDialog:
    """Password generator dialog with configurable options."""

    def __init__(self, app, target_entry):
        self.app = app
        self.target_entry = target_entry
        p = app.palette

        self.win = tk.Toplevel(app.root)
        self.win.title("Password Generator")
        self.win.geometry("400x300")
        self.win.resizable(False, False)
        self.win.transient(app.root)
        self.win.grab_set()

        main = ttk.Frame(self.win)
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Length
        ttk.Label(main, text="Password Length",
            font=("", 11, "bold")).pack(anchor=tk.W)

        length_row = ttk.Frame(main)
        length_row.pack(fill=tk.X, pady=(4, 10))

        self.length_var = tk.IntVar(value=24)
        self.length_scale = ttk.Scale(length_row, from_=12, to=64,
            variable=self.length_var, orient=tk.HORIZONTAL,
            command=self._on_option_change)
        self.length_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.length_label = ttk.Label(length_row, text="24",
            font=("", 11), width=3)
        self.length_label.pack(side=tk.RIGHT, padx=(10, 0))

        # Character sets
        ttk.Label(main, text="Character Sets",
            font=("", 11, "bold")).pack(anchor=tk.W, pady=(0, 4))

        self.use_upper = tk.BooleanVar(value=True)
        self.use_lower = tk.BooleanVar(value=True)
        self.use_digits = tk.BooleanVar(value=True)
        self.use_symbols = tk.BooleanVar(value=True)

        checks_row = ttk.Frame(main)
        checks_row.pack(fill=tk.X, pady=(0, 10))

        for text, var in [("Uppercase", self.use_upper),
                          ("Lowercase", self.use_lower),
                          ("Digits", self.use_digits),
                          ("Symbols", self.use_symbols)]:
            app.checkbox(checks_row, text, var,
                command=self._on_option_change)

        # Generated password
        ttk.Label(main, text="Generated Password",
            font=("", 11, "bold")).pack(anchor=tk.W, pady=(0, 4))

        self.password_entry = tk.Entry(main,
            font=("", 12), bg=p["entry_bg"], fg=p["entry_fg"],
            relief=tk.FLAT, highlightbackground=p["highlight_border"],
            highlightthickness=1, insertbackground=p["insert_bg"],
            state='readonly')
        self.password_entry.pack(fill=tk.X, pady=(0, 15))

        # Buttons
        btn_row = ttk.Frame(main)
        btn_row.pack(fill=tk.X)

        ttk.Button(btn_row, text="Use",
            command=self._use_password, default="active"
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(btn_row, text="Copy",
            command=self._copy_password
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(btn_row, text="Regenerate",
            command=self._generate
        ).pack(side=tk.RIGHT)

        # Generate initial password
        self._generate()

    def _on_option_change(self, *args):
        length = self.length_var.get()
        self.length_label.config(text=str(length))
        self._generate()

    def _generate(self):
        charset = ""
        if self.use_upper.get():
            charset += string.ascii_uppercase
        if self.use_lower.get():
            charset += string.ascii_lowercase
        if self.use_digits.get():
            charset += string.digits
        if self.use_symbols.get():
            charset += string.punctuation

        if not charset:
            charset = string.ascii_letters + string.digits

        length = self.length_var.get()
        password = "".join(secrets.choice(charset) for _ in range(length))

        self.password_entry.config(state=tk.NORMAL)
        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, password)
        self.password_entry.config(state='readonly')

    def _copy_password(self):
        password = self.password_entry.get()
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append(password)

    def _use_password(self):
        password = self.password_entry.get()
        self.target_entry.delete(0, tk.END)
        self.target_entry.insert(0, password)
        self.win.destroy()
