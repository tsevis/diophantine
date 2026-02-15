import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import os
import hashlib

from crypto.zip_engine import create_encrypted_zip
from crypto.veracrypt_engine import create_veracrypt_container
from crypto.sevenz_engine import create_encrypted_7z
from crypto.gpg_engine import create_gpg_encrypted
from utils.naming import original_name, numeric_name, chronos_name
from utils.entropy import calculate_entropy, entropy_to_strength
from utils.recovery_phrase import generate_recovery_phrase
from utils.keyfile_auth import (
    generate_keyfile, load_keyfile, validate_keyfile,
    combine_keyfile_and_password
)
from utils.profiles import save_profile, load_profile, list_profiles, delete_profile

# Extension map for each encryption method
EXT_MAP = {
    "zip": ".zip",
    "7z": ".7z",
    "gpg": ".tar.gpg",
    "veracrypt": ".hc",
}


class EncryptTab:
    """Encrypt tab: file selection, options, and encryption execution."""

    def __init__(self, parent_notebook, app):
        self.app = app
        self.root = app.root
        self.items = []
        self.current_keyfile = None
        self.advanced_enabled = tk.BooleanVar()
        self.show_password_var = tk.BooleanVar()

        self.frame = ttk.Frame(parent_notebook)
        self._build()

    def _build(self):
        ui = self.app
        p = ui.palette

        # ── Action Bar ───────────────────────────────────────────
        action_bar = ttk.Frame(self.frame)
        action_bar.pack(fill=tk.X)

        ttk.Button(action_bar, text="Encrypt",
            command=self.encrypt, default="active"
        ).pack(side=tk.RIGHT, padx=(5, 20), pady=8)

        for label, cmd in [("Remove", self.remove_item),
                           ("Add Folder", self.add_folder),
                           ("Add Files", self.add_files)]:
            ttk.Button(action_bar, text=label, command=cmd
            ).pack(side=tk.RIGHT, padx=3, pady=8)

        # ── Profile controls (left side of action bar) ───────────
        ttk.Label(action_bar, text="Profile:",
            font=("", 10)).pack(side=tk.LEFT, padx=(20, 5), pady=8)

        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(action_bar,
            textvariable=self.profile_var,
            state='readonly', width=15, font=("", 10))
        self.profile_combo.pack(side=tk.LEFT, padx=2, pady=8)
        self.profile_combo.bind("<<ComboboxSelected>>", self._on_profile_select)
        self._refresh_profiles()

        ttk.Button(action_bar, text="Save",
            command=self._save_profile
        ).pack(side=tk.LEFT, padx=2, pady=8)

        ttk.Button(action_bar, text="Delete",
            command=self._delete_profile
        ).pack(side=tk.LEFT, padx=2, pady=8)

        ttk.Separator(self.frame, orient="horizontal").pack(fill=tk.X)

        # ── Content ──────────────────────────────────────────────
        content = ttk.Frame(self.frame)
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Two-column options
        options_row = ttk.Frame(content)
        options_row.pack(fill=tk.X)
        options_row.columnconfigure(0, weight=1, uniform="col")
        options_row.columnconfigure(1, weight=1, uniform="col")

        # ── Column 1: Basic Options ──────────────────────────────
        basic = ttk.LabelFrame(options_row, text="  Basic Options  ")
        basic.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # Inner padding frame
        basic_inner = ttk.Frame(basic)
        basic_inner.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        self.single_archive = tk.BooleanVar()
        ui.checkbox(basic_inner, "Create single archive",
            self.single_archive)

        ui.section_label(basic_inner, "Encryption Method")
        self.encryption_method = tk.StringVar(value="zip")
        self.encryption_method.trace_add("write", self._on_method_change)
        ui.radio(basic_inner, "ZIP (AES-256)", self.encryption_method, "zip")
        ui.radio(basic_inner, "7z (AES-256)", self.encryption_method, "7z")
        ui.radio(basic_inner, "GPG (AES-256)", self.encryption_method, "gpg")
        ui.radio(basic_inner, "VeraCrypt Container", self.encryption_method, "veracrypt")

        self.size_estimate_label = ttk.Label(basic_inner, text="",
            font=("", 9))
        self.size_estimate_label.pack(anchor=tk.W, pady=(2, 0))

        ui.section_label(basic_inner, "Naming Scheme")
        self.naming_scheme = tk.StringVar(value="original")
        ui.radio(basic_inner, "Original Name", self.naming_scheme, "original")
        ui.radio(basic_inner, "Numeric", self.naming_scheme, "numeric")
        ui.radio(basic_inner, "Chronological", self.naming_scheme, "chronos")

        ui.section_label(basic_inner, "Password")

        pw_row = ttk.Frame(basic_inner)
        pw_row.pack(fill=tk.X, pady=(0, 2))

        self.password = tk.Entry(pw_row, show="*",
            font=("", 11), bg=p["entry_bg"], fg=p["entry_fg"],
            relief=tk.FLAT, highlightbackground=p["highlight_border"],
            highlightthickness=1, insertbackground=p["insert_bg"])
        self.password.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(pw_row, text="Show",
            command=self.toggle_password_visibility
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(pw_row, text="Generate",
            command=self._open_password_generator
        ).pack(side=tk.RIGHT, padx=(5, 0))

        self.strength = ttk.Label(basic_inner, text="",
            font=("", 9))
        self.strength.pack(anchor=tk.W, pady=(2, 0))
        self.password.bind("<KeyRelease>", self.update_strength)

        # ── Column 2: Advanced Options ───────────────────────────
        advanced = ttk.LabelFrame(options_row, text="  Advanced Options  ")
        advanced.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        adv_inner = ttk.Frame(advanced)
        adv_inner.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        self.advanced_checkbox = ui.checkbox(adv_inner,
            "Enable Advanced Features", self.advanced_enabled,
            command=self.toggle_advanced_mode)

        ui.section_label(adv_inner, "Recovery Phrase")

        self.generate_phrase_btn = ttk.Button(adv_inner, text="Generate",
            command=self.generate_recovery_phrase, state=tk.DISABLED)
        self.generate_phrase_btn.pack(anchor=tk.W, pady=(0, 4))

        self.recovery_phrase_display = tk.Text(adv_inner,
            height=2, font=("", 9),
            bg=p["text_bg"], fg=p["text_fg"], relief=tk.FLAT,
            highlightbackground=p["highlight_border"], highlightthickness=1,
            wrap=tk.WORD, state=tk.DISABLED)
        self.recovery_phrase_display.pack(fill=tk.X, pady=(0, 2))

        self.recovery_phrase_warning = ttk.Label(adv_inner,
            text="Write this down and keep it secure!",
            font=("", 8), foreground=p["warning_fg"])
        self.recovery_phrase_warning.pack(anchor=tk.W)

        ui.section_label(adv_inner, "Keyfile Authentication")

        kf_row = ttk.Frame(adv_inner)
        kf_row.pack(fill=tk.X, pady=(0, 4))

        self.generate_keyfile_btn = ttk.Button(kf_row,
            text="Generate Keyfile", command=self.generate_keyfile,
            state=tk.DISABLED)
        self.generate_keyfile_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.use_keyfile_btn = ttk.Button(kf_row,
            text="Use Keyfile", command=self.select_keyfile,
            state=tk.DISABLED)
        self.use_keyfile_btn.pack(side=tk.LEFT)

        self.use_two_factor = tk.BooleanVar()
        self.two_factor_checkbox = ui.checkbox(adv_inner,
            "Two-Factor (Keyfile + Password)",
            self.use_two_factor)
        self.two_factor_checkbox.config(state=tk.DISABLED)

        self.keyfile_info = ttk.Label(adv_inner,
            text="No keyfile selected",
            font=("", 9), foreground=p["light_text"])
        self.keyfile_info.pack(anchor=tk.W, pady=(2, 0))

        # ── File List ────────────────────────────────────────────
        ttk.Separator(content, orient="horizontal").pack(
            fill=tk.X, pady=(12, 0))

        list_header = ttk.Frame(content)
        list_header.pack(fill=tk.X, pady=(8, 4))

        ttk.Label(list_header, text="Items to Encrypt",
            font=("", 11, "bold")
        ).pack(side=tk.LEFT)

        self.item_count_label = ttk.Label(list_header,
            text="Drag and drop files here",
            font=("", 9))
        self.item_count_label.pack(side=tk.RIGHT)

        list_frame = ttk.Frame(content)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(list_frame,
            bg=p["listbox_bg"], fg=p["listbox_fg"],
            selectbackground=p["select_bg"], selectforeground=p["select_fg"],
            highlightbackground=p["highlight_border"], highlightthickness=1,
            relief=tk.FLAT, borderwidth=1,
            yscrollcommand=scrollbar.set,
            font=("", 11), selectmode=tk.EXTENDED)
        self.listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        # Store default appearance for DnD restore
        self._listbox_default_bg = p["listbox_bg"]
        self._listbox_default_border = p["highlight_border"]

        self.listbox.drop_target_register("DND_Files")
        self.listbox.dnd_bind("<<Drop>>", self.drop)
        self.listbox.dnd_bind("<<DropEnter>>", self._on_drop_enter)
        self.listbox.dnd_bind("<<DropLeave>>", self._on_drop_leave)

    # ── File Management ──────────────────────────────────────────

    def _update_item_count(self):
        count = len(self.items)
        if count == 0:
            self.item_count_label.config(text="Drag and drop files here")
        elif count == 1:
            self.item_count_label.config(text="1 item")
        else:
            self.item_count_label.config(text=f"{count} items")
        self._update_size_estimate()

    def add_files(self):
        paths = filedialog.askopenfilenames(title="Select files")
        for p in paths:
            if p and p not in self.items:
                self.items.append(p)
                self.listbox.insert(tk.END, p)
        self._update_item_count()

    def add_folder(self):
        folder = filedialog.askdirectory(title="Select folder")
        if folder:
            if folder not in self.items:
                self.items.append(folder)
                self.listbox.insert(tk.END, folder)
        self._update_item_count()

    def remove_item(self):
        selected_indices = self.listbox.curselection()
        for index in reversed(selected_indices):
            item = self.listbox.get(index)
            self.items.remove(item)
            self.listbox.delete(index)
        self._update_item_count()

    def drop(self, event):
        self._restore_listbox_appearance()
        if event.data:
            files = self.root.tk.splitlist(event.data)
            for path in files:
                if os.path.exists(path) and path not in self.items:
                    self.items.append(path)
                    self.listbox.insert(tk.END, path)
        self._update_item_count()

    # ── DnD Visual Feedback ──────────────────────────────────────

    def _on_drop_enter(self, event):
        p = self.app.palette
        self.listbox.config(
            highlightbackground=p["accent"],
            highlightthickness=2,
            bg=p["drop_highlight_bg"])
        return event.action

    def _on_drop_leave(self, event):
        self._restore_listbox_appearance()

    def _restore_listbox_appearance(self):
        self.listbox.config(
            highlightbackground=self._listbox_default_border,
            highlightthickness=1,
            bg=self._listbox_default_bg)

    # ── Container Size Estimation ────────────────────────────────

    def _calculate_total_size(self):
        """Recursively sum file sizes for all items."""
        total = 0
        for item in self.items:
            if os.path.isfile(item):
                total += os.path.getsize(item)
            elif os.path.isdir(item):
                for dirpath, _, filenames in os.walk(item):
                    for f in filenames:
                        total += os.path.getsize(os.path.join(dirpath, f))
        return total

    def _update_size_estimate(self):
        """Show estimated container size when VeraCrypt is selected."""
        if self.encryption_method.get() == "veracrypt" and self.items:
            total = self._calculate_total_size()
            # 10% overhead, minimum 10MB
            estimated_mb = max(10, int(total * 1.1 / (1024 * 1024)) + 1)
            self.size_estimate_label.config(
                text=f"Estimated container size: {estimated_mb} MB")
        else:
            self.size_estimate_label.config(text="")

    def _on_method_change(self, *args):
        self._update_size_estimate()

    # ── Profiles ─────────────────────────────────────────────────

    def _refresh_profiles(self):
        names = list_profiles()
        self.profile_combo["values"] = names
        if not names:
            self.profile_var.set("")

    def _save_profile(self):
        name = simpledialog.askstring("Save Profile",
            "Profile name:", parent=self.root)
        if not name:
            return
        settings = {
            "encryption_method": self.encryption_method.get(),
            "naming_scheme": self.naming_scheme.get(),
            "single_archive": self.single_archive.get(),
            "advanced_enabled": self.advanced_enabled.get(),
            "keyfile_path": self.current_keyfile or "",
            "use_two_factor": self.use_two_factor.get(),
        }
        save_profile(name, settings)
        self._refresh_profiles()
        self.profile_var.set(name)
        messagebox.showinfo("Diophantine", f"Profile '{name}' saved.")

    def _on_profile_select(self, event=None):
        name = self.profile_var.get()
        if not name:
            return
        settings = load_profile(name)
        if settings is None:
            return
        self.encryption_method.set(settings.get("encryption_method", "zip"))
        self.naming_scheme.set(settings.get("naming_scheme", "original"))
        self.single_archive.set(settings.get("single_archive", False))
        self.advanced_enabled.set(settings.get("advanced_enabled", False))
        self.toggle_advanced_mode()
        kf = settings.get("keyfile_path", "")
        if kf and os.path.isfile(kf):
            self.current_keyfile = kf
            self.keyfile_info.config(
                text=f"Keyfile: {os.path.basename(kf)}",
                foreground=self.app.palette["info_fg"])
        self.use_two_factor.set(settings.get("use_two_factor", False))

    def _delete_profile(self):
        name = self.profile_var.get()
        if not name:
            messagebox.showwarning("Diophantine", "No profile selected.")
            return
        if messagebox.askyesno("Diophantine",
                f"Delete profile '{name}'?"):
            delete_profile(name)
            self._refresh_profiles()
            messagebox.showinfo("Diophantine", f"Profile '{name}' deleted.")

    # ── Password Generator ───────────────────────────────────────

    def _open_password_generator(self):
        from ui.password_generator import PasswordGeneratorDialog
        PasswordGeneratorDialog(self.app, self.password)

    # ── Advanced Features ────────────────────────────────────────

    def generate_recovery_phrase(self):
        phrase_words = generate_recovery_phrase(128)
        phrase = " ".join(phrase_words)
        self.recovery_phrase_display.config(state=tk.NORMAL)
        self.recovery_phrase_display.delete(1.0, tk.END)
        self.recovery_phrase_display.insert(1.0, phrase)
        self.recovery_phrase_display.config(state=tk.DISABLED)
        p = self.app.palette
        self.strength.config(
            text="Recovery phrase generated. Use for account recovery.",
            foreground=p["info_fg"])
        self.root.after(10000,
            lambda: self.strength.config(text=""))

    def toggle_advanced_mode(self):
        if self.advanced_enabled.get():
            self.generate_phrase_btn.state(['!disabled'])
            self.recovery_phrase_display.config(state=tk.NORMAL)
            self.generate_keyfile_btn.state(['!disabled'])
            self.use_keyfile_btn.state(['!disabled'])
            self.two_factor_checkbox.config(state=tk.NORMAL)
        else:
            self.generate_phrase_btn.state(['disabled'])
            self.recovery_phrase_display.config(state=tk.DISABLED)
            self.generate_keyfile_btn.state(['disabled'])
            self.use_keyfile_btn.state(['disabled'])
            self.two_factor_checkbox.config(state=tk.DISABLED)

    def generate_keyfile(self):
        file_path = filedialog.asksaveasfilename(
            title="Save Keyfile",
            defaultextension=".diophantus",
            filetypes=[("Diophantus Keyfiles", "*.diophantus"),
                       ("All files", "*.*")])
        if file_path:
            try:
                generate_keyfile(file_path)
                self.current_keyfile = file_path
                p = self.app.palette
                self.keyfile_info.config(
                    text=f"Keyfile: {os.path.basename(file_path)}",
                    foreground=p["info_fg"])
                messagebox.showinfo("Success",
                    f"Keyfile generated successfully:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error",
                    f"Failed to generate keyfile:\n{str(e)}")

    def select_keyfile(self):
        file_path = filedialog.askopenfilename(
            title="Select Keyfile",
            filetypes=[("Diophantus Keyfiles", "*.diophantus"),
                       ("All files", "*.*")])
        if file_path:
            try:
                p = self.app.palette
                if validate_keyfile(file_path):
                    self.current_keyfile = file_path
                    self.keyfile_info.config(
                        text=f"Keyfile: {os.path.basename(file_path)}",
                        foreground=p["info_fg"])
                else:
                    messagebox.showerror("Error",
                        "Selected file is not a valid keyfile.")
                    self.keyfile_info.config(
                        text="Invalid keyfile selected",
                        foreground=p["warning_fg"])
            except Exception as e:
                messagebox.showerror("Error",
                    f"Error validating keyfile:\n{str(e)}")
                self.keyfile_info.config(
                    text="Error validating keyfile",
                    foreground=self.app.palette["warning_fg"])

    # ── Authentication ───────────────────────────────────────────

    def toggle_password_visibility(self):
        self.show_password_var.set(not self.show_password_var.get())
        self.password.config(
            show="" if self.show_password_var.get() else "*")

    def update_strength(self, _):
        password = self.password.get()
        entropy = calculate_entropy(password)
        strength_label, color = entropy_to_strength(entropy)
        self.strength.config(
            text=f"Entropy: {entropy:.1f} bits ({strength_label})",
            foreground=color)

    # ── Encrypt ──────────────────────────────────────────────────

    def encrypt(self):
        if not self.items:
            messagebox.showerror("Diophantine", "No files selected.")
            return

        password = ""

        recovery_text = ""
        if self.advanced_enabled.get():
            try:
                recovery_text = self.recovery_phrase_display.get(
                    1.0, tk.END).strip()
            except:
                recovery_text = ""

        if recovery_text:
            password = recovery_text
        elif (self.current_keyfile and self.use_two_factor.get()
                and self.advanced_enabled.get()):
            if not validate_keyfile(self.current_keyfile):
                messagebox.showerror("Error",
                    "Keyfile is invalid or corrupted.")
                return

            password_input = self.password.get()
            if not password_input:
                messagebox.showerror("Error",
                    "Password required for two-factor authentication.")
                return

            password = combine_keyfile_and_password(
                self.current_keyfile, password_input)
        elif (self.current_keyfile
              and not self.use_two_factor.get()
              and self.advanced_enabled.get()):
            if not validate_keyfile(self.current_keyfile):
                messagebox.showerror("Error",
                    "Keyfile is invalid or corrupted.")
                return

            keyfile_data = load_keyfile(self.current_keyfile)
            password = hashlib.sha256(keyfile_data).hexdigest()
        else:
            password = self.password.get()

            if not recovery_text:
                entropy = calculate_entropy(password)
                if entropy < 50:
                    if not messagebox.askyesno("Diophantine",
                            "Password entropy is low. "
                            "Continue anyway?"):
                        return

        output_dir = filedialog.askdirectory()
        if not output_dir:
            return

        method = self.encryption_method.get()
        ext = EXT_MAP.get(method, ".zip")

        # Reset progress
        self.app.progress["value"] = 0
        self.app.progress["maximum"] = len(self.items) or 100
        self.root.update_idletasks()

        try:
            if method == "veracrypt":
                out = os.path.join(output_dir, "diophantine.hc")
                create_veracrypt_container(self.items, out, password)
            elif method == "gpg":
                if self.single_archive.get() or len(self.items) > 1:
                    out = os.path.join(output_dir, "diophantine.tar.gpg")
                    create_gpg_encrypted(
                        self.items, out, password, single_archive=True)
                else:
                    for i, item in enumerate(self.items, start=1):
                        if self.naming_scheme.get() == "original":
                            filename = original_name(item, ext=".gpg")
                        elif self.naming_scheme.get() == "numeric":
                            filename = numeric_name(i, ext=".gpg")
                        elif self.naming_scheme.get() == "chronos":
                            filename = chronos_name(i, ext=".gpg")
                        else:
                            filename = original_name(item, ext=".gpg")

                        out = os.path.join(output_dir, filename)
                        create_gpg_encrypted(
                            [item], out, password, single_archive=False)
                        self.app.progress["value"] = i
                        self.root.update_idletasks()
            elif method == "7z":
                if self.single_archive.get():
                    out = os.path.join(output_dir, "diophantine.7z")
                    create_encrypted_7z(self.items, out, password)
                else:
                    for i, item in enumerate(self.items, start=1):
                        if self.naming_scheme.get() == "original":
                            filename = original_name(item, ext=ext)
                        elif self.naming_scheme.get() == "numeric":
                            filename = numeric_name(i, ext=ext)
                        elif self.naming_scheme.get() == "chronos":
                            filename = chronos_name(i, ext=ext)
                        else:
                            filename = original_name(item, ext=ext)

                        out = os.path.join(output_dir, filename)
                        create_encrypted_7z([item], out, password)
                        self.app.progress["value"] = i
                        self.root.update_idletasks()
            else:
                # ZIP
                if self.single_archive.get():
                    out = os.path.join(output_dir, "diophantine.zip")
                    create_encrypted_zip(
                        self.items, out, password, single_archive=True)
                else:
                    for i, item in enumerate(self.items, start=1):
                        if self.naming_scheme.get() == "original":
                            filename = original_name(item, ext=ext)
                        elif self.naming_scheme.get() == "numeric":
                            filename = numeric_name(i, ext=ext)
                        elif self.naming_scheme.get() == "chronos":
                            filename = chronos_name(i, ext=ext)
                        else:
                            filename = original_name(item, ext=ext)

                        out = os.path.join(output_dir, filename)
                        create_encrypted_zip(
                            [item], out, password, single_archive=False)
                        self.app.progress["value"] = i
                        self.root.update_idletasks()

            self.app.progress["value"] = self.app.progress["maximum"]
            self.root.update_idletasks()
            messagebox.showinfo("Diophantine", "Encryption complete.")
        except Exception as e:
            messagebox.showerror("Diophantine",
                f"Encryption failed:\n{str(e)}")
