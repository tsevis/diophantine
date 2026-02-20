import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import hashlib

from crypto.zip_engine import extract_encrypted_zip
from crypto.veracrypt_engine import (
    mount_veracrypt_container,
    unmount_veracrypt_container,
    extract_veracrypt_container
)
from crypto.sevenz_engine import extract_encrypted_7z
from crypto.gpg_engine import extract_gpg_encrypted
from utils.keyfile_auth import (
    load_keyfile, validate_keyfile, combine_keyfile_and_password
)
from utils.recovery_phrase import validate_recovery_phrase


# Extension-to-type mapping for auto-detection
FILE_TYPE_MAP = {
    '.zip': 'zip',
    '.hc': 'veracrypt',
    '.tc': 'veracrypt',
    '.7z': '7z',
    '.gpg': 'gpg',
    '.pgp': 'gpg',
    '.asc': 'gpg',
}

TYPE_DISPLAY = {
    'zip': 'ZIP (AES-256)',
    '7z': '7z (AES-256)',
    'gpg': 'GPG (AES-256)',
    'veracrypt': 'VeraCrypt Container',
}


class DecryptTab:
    """Decrypt/Unlock tab: batch file list, authenticate, decrypt."""

    def __init__(self, parent_notebook, app):
        self.app = app
        self.root = app.root

        # State
        self.items = []
        self.manual_file_type = tk.StringVar(value="auto")
        self.show_password_var = tk.BooleanVar()
        self.use_keyfile = tk.BooleanVar()
        self.use_recovery_phrase = tk.BooleanVar()
        self.current_keyfile = None
        self.veracrypt_mode = tk.StringVar(value="extract")
        self.output_dir = tk.StringVar()
        self.current_mount = None

        self.frame = ttk.Frame(parent_notebook)
        self._build()

    def _build(self):
        ui = self.app
        p = ui.palette

        # ── Action Bar ───────────────────────────────────────────
        action_bar = ttk.Frame(self.frame)
        action_bar.pack(fill=tk.X)

        self.decrypt_btn = ttk.Button(action_bar, text="Decrypt",
            command=self.decrypt, default="active")
        self.decrypt_btn.pack(side=tk.RIGHT, padx=(5, 20), pady=8)

        self.unmount_btn = ttk.Button(action_bar, text="Unmount",
            command=self._unmount_current)
        # Hidden initially
        self.unmount_btn.pack_forget()

        ttk.Button(action_bar, text="Remove",
            command=self.remove_item
        ).pack(side=tk.RIGHT, padx=3, pady=8)

        ttk.Button(action_bar, text="Add Files",
            command=self.browse_encrypted_files
        ).pack(side=tk.RIGHT, padx=3, pady=8)

        ttk.Separator(self.frame, orient="horizontal").pack(fill=tk.X)

        # ── Content ──────────────────────────────────────────────
        content = ttk.Frame(self.frame)
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Two-column layout
        options_row = ttk.Frame(content)
        options_row.pack(fill=tk.X)
        options_row.columnconfigure(0, weight=1, uniform="col")
        options_row.columnconfigure(1, weight=1, uniform="col")

        # ── Column 1: File & Options ─────────────────────────────
        left = ttk.LabelFrame(options_row, text="  File & Options  ")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        left_inner = ttk.Frame(left)
        left_inner.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        self._build_type_detection(left_inner)
        self._build_veracrypt_options(left_inner)
        self._build_output_selection(left_inner)

        # ── Column 2: Authentication ─────────────────────────────
        right = ttk.LabelFrame(options_row, text="  Authentication  ")
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        right_inner = ttk.Frame(right)
        right_inner.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        self._build_password_input(right_inner)
        self._build_keyfile_option(right_inner)
        self._build_recovery_phrase_input(right_inner)

        # ── File List ────────────────────────────────────────────
        ttk.Separator(content, orient="horizontal").pack(
            fill=tk.X, pady=(12, 0))

        list_header = ttk.Frame(content)
        list_header.pack(fill=tk.X, pady=(8, 4))

        ttk.Label(list_header, text="Encrypted Files",
            font=("", 11, "bold")
        ).pack(side=tk.LEFT)

        self.item_count_label = ttk.Label(list_header,
            text="Drag and drop encrypted files here",
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
        self.listbox.dnd_bind("<<Drop>>", self._on_drop)
        self.listbox.dnd_bind("<<DropEnter>>", self._on_drop_enter)
        self.listbox.dnd_bind("<<DropLeave>>", self._on_drop_leave)

    # ── Sub-builders ─────────────────────────────────────────────

    def _build_type_detection(self, parent):
        ui = self.app
        ui.section_label(parent, "File Type")

        type_row = ttk.Frame(parent)
        type_row.pack(fill=tk.X, pady=(0, 4))

        self.type_label = ttk.Label(type_row, text="No files selected",
            font=("", 10), foreground=ui.palette["light_text"])
        self.type_label.pack(side=tk.LEFT)

        self.type_override = ttk.Combobox(type_row,
            textvariable=self.manual_file_type,
            values=["auto", "zip", "7z", "veracrypt", "gpg"],
            state='readonly', width=10,
            font=("", 10))
        self.type_override.pack(side=tk.RIGHT)
        self.type_override.bind("<<ComboboxSelected>>",
            self._on_type_change)

        ttk.Label(type_row, text="Override:",
            font=("", 9)).pack(side=tk.RIGHT, padx=(0, 5))

    def _build_veracrypt_options(self, parent):
        ui = self.app

        # Container frame always packed in position; contents shown/hidden
        self.vc_container = ttk.Frame(parent)
        self.vc_container.pack(fill=tk.X)

        self.vc_label = ttk.Label(self.vc_container, text="VeraCrypt Mode",
            font=("", 10, "bold"))

        self.vc_frame = ttk.Frame(self.vc_container)

        ui.radio(self.vc_frame,
            "Mount + Extract + Unmount (automated)",
            self.veracrypt_mode, "extract",
            command=self._update_decrypt_btn_text)
        ui.radio(self.vc_frame,
            "Mount only (manual access)",
            self.veracrypt_mode, "mount",
            command=self._update_decrypt_btn_text)

        # Hidden initially

    def _build_output_selection(self, parent):
        ui = self.app
        ui.section_label(parent, "Output Directory")
        p = ui.palette

        out_row = ttk.Frame(parent)
        out_row.pack(fill=tk.X, pady=(0, 4))

        self.output_entry = tk.Entry(out_row,
            textvariable=self.output_dir,
            font=("", 11), bg=p["entry_bg"], fg=p["entry_fg"],
            relief=tk.FLAT, highlightbackground=p["highlight_border"],
            highlightthickness=1, insertbackground=p["insert_bg"],
            state='readonly')
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(out_row, text="Browse",
            command=self.browse_output_dir
        ).pack(side=tk.RIGHT, padx=(5, 0))

    def _build_password_input(self, parent):
        ui = self.app
        p = ui.palette
        ui.section_label(parent, "Password")

        pw_row = ttk.Frame(parent)
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

    def _build_keyfile_option(self, parent):
        ui = self.app
        p = ui.palette
        ui.section_label(parent, "Keyfile Authentication")

        ui.checkbox(parent, "Use Keyfile", self.use_keyfile,
            command=self._toggle_keyfile)

        self.select_keyfile_btn = ttk.Button(parent,
            text="Select Keyfile", command=self.select_keyfile,
            state=tk.DISABLED)
        self.select_keyfile_btn.pack(anchor=tk.W, padx=(18, 0), pady=(0, 2))

        self.keyfile_info = ttk.Label(parent,
            text="No keyfile selected",
            font=("", 9), foreground=p["light_text"])
        self.keyfile_info.pack(anchor=tk.W, pady=(2, 0))

    def _build_recovery_phrase_input(self, parent):
        ui = self.app
        p = ui.palette
        ui.section_label(parent, "Recovery Phrase")

        ui.checkbox(parent, "Use Recovery Phrase",
            self.use_recovery_phrase,
            command=self._toggle_recovery)

        self.recovery_input = tk.Text(parent,
            height=2, font=("", 9),
            bg=p["text_bg"], fg=p["text_fg"], relief=tk.FLAT,
            highlightbackground=p["highlight_border"], highlightthickness=1,
            wrap=tk.WORD, state=tk.DISABLED)
        self.recovery_input.pack(fill=tk.X, pady=(0, 2))

        ttk.Label(parent,
            text="Enter the recovery phrase used during encryption",
            font=("", 8)).pack(anchor=tk.W)

    # ── File Management ──────────────────────────────────────────

    def _update_item_count(self):
        count = len(self.items)
        if count == 0:
            self.item_count_label.config(text="Drag and drop encrypted files here")
        elif count == 1:
            self.item_count_label.config(text="1 file")
        else:
            self.item_count_label.config(text=f"{count} files")
        self._update_type_display()

    def browse_encrypted_files(self):
        paths = filedialog.askopenfilenames(
            title="Select encrypted files",
            filetypes=[
                ("Encrypted files", "*.zip *.hc *.tc *.7z *.gpg *.pgp *.asc"),
                ("ZIP archives", "*.zip"),
                ("7z archives", "*.7z"),
                ("GPG files", "*.gpg *.pgp *.asc"),
                ("VeraCrypt containers", "*.hc *.tc"),
                ("All files", "*.*")
            ])
        for path in paths:
            if path and path not in self.items:
                self.items.append(path)
                self.listbox.insert(tk.END, path)
        self._update_item_count()

    def remove_item(self):
        selected_indices = self.listbox.curselection()
        for index in reversed(selected_indices):
            item = self.listbox.get(index)
            self.items.remove(item)
            self.listbox.delete(index)
        self._update_item_count()

    def browse_output_dir(self):
        directory = filedialog.askdirectory(title="Select output directory")
        if directory:
            self.output_dir.set(directory)

    def _on_drop(self, event):
        self._restore_listbox_appearance()
        if event.data:
            files = self.root.tk.splitlist(event.data)
            for path in files:
                if os.path.isfile(path) and path not in self.items:
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

    # ── Type Detection ───────────────────────────────────────────

    def _detect_type(self, path):
        """Detect file type from extension."""
        ext = os.path.splitext(path)[1].lower()
        # Handle .tar.gpg
        if path.lower().endswith(".tar.gpg"):
            return "gpg"
        return FILE_TYPE_MAP.get(ext, "unknown")

    def _update_type_display(self):
        """Update the type label based on current files."""
        if not self.items:
            self.type_label.config(
                text="No files selected",
                foreground=self.app.palette["light_text"])
            self._hide_veracrypt_options()
            return

        types = set()
        for item in self.items:
            types.add(self._detect_type(item))

        if len(types) == 1:
            t = types.pop()
            if t == "unknown":
                self.type_label.config(
                    text="Unknown type. Select manually.",
                    foreground=self.app.palette["warning_fg"])
            else:
                display = TYPE_DISPLAY.get(t, t)
                self.type_label.config(
                    text=f"Detected: {display}",
                    foreground=self.app.palette["info_fg"])
        else:
            self.type_label.config(
                text="Mixed file types",
                foreground=self.app.palette["info_fg"])

        self._update_veracrypt_visibility()

    def _on_type_change(self, event=None):
        self._update_veracrypt_visibility()

    def _get_effective_type(self, path=None):
        """Get the effective type for a file, considering manual override."""
        manual = self.manual_file_type.get()
        if manual != "auto":
            return manual
        if path:
            return self._detect_type(path)
        # Fallback: check first item
        if self.items:
            return self._detect_type(self.items[0])
        return ""

    def _update_veracrypt_visibility(self):
        has_veracrypt = False
        if self.manual_file_type.get() == "veracrypt":
            has_veracrypt = True
        elif self.manual_file_type.get() == "auto":
            for item in self.items:
                if self._detect_type(item) == "veracrypt":
                    has_veracrypt = True
                    break

        if has_veracrypt:
            self.vc_label.pack(in_=self.vc_container,
                anchor=tk.W, pady=(10, 3))
            self.vc_frame.pack(in_=self.vc_container,
                fill=tk.X, pady=(0, 4))
            self._update_decrypt_btn_text()
        else:
            self._hide_veracrypt_options()
            self.decrypt_btn.config(text="Decrypt")

    def _hide_veracrypt_options(self):
        self.vc_label.pack_forget()
        self.vc_frame.pack_forget()

    def _update_decrypt_btn_text(self):
        has_veracrypt = False
        if self.manual_file_type.get() == "veracrypt":
            has_veracrypt = True
        elif self.manual_file_type.get() == "auto":
            for item in self.items:
                if self._detect_type(item) == "veracrypt":
                    has_veracrypt = True
                    break

        if has_veracrypt and self.veracrypt_mode.get() == "mount":
            self.decrypt_btn.config(text="Mount")
        else:
            self.decrypt_btn.config(text="Decrypt")

    # ── Password Generator ───────────────────────────────────────

    def _open_password_generator(self):
        from ui.password_generator import PasswordGeneratorDialog
        PasswordGeneratorDialog(self.app, self.password)

    # ── Event Handlers ───────────────────────────────────────────

    def toggle_password_visibility(self):
        self.show_password_var.set(not self.show_password_var.get())
        self.password.config(
            show="" if self.show_password_var.get() else "*")

    def _toggle_keyfile(self):
        if self.use_keyfile.get():
            self.select_keyfile_btn.state(['!disabled'])
        else:
            self.select_keyfile_btn.state(['disabled'])
            self.current_keyfile = None
            self.keyfile_info.config(
                text="No keyfile selected",
                foreground=self.app.palette["light_text"])

    def _toggle_recovery(self):
        if self.use_recovery_phrase.get():
            self.recovery_input.config(state=tk.NORMAL)
            self.password.config(state=tk.DISABLED)
        else:
            self.recovery_input.config(state=tk.DISABLED)
            self.password.config(state=tk.NORMAL)

    def select_keyfile(self):
        file_path = filedialog.askopenfilename(
            title="Select Keyfile",
            filetypes=[("Diophantus Keyfiles", "*.diophantus"),
                       ("All files", "*.*")])
        if file_path:
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

    def _unmount_current(self):
        if self.current_mount:
            try:
                unmount_veracrypt_container(self.current_mount)
                messagebox.showinfo("Diophantine",
                    f"Container unmounted from:\n{self.current_mount}")
                self.current_mount = None
                self.unmount_btn.pack_forget()
            except Exception as e:
                messagebox.showerror("Error",
                    f"Failed to unmount:\n{str(e)}")

    # ── Password Resolution ──────────────────────────────────────

    def _resolve_password(self):
        """Resolve the decryption password from all auth sources."""

        if self.use_recovery_phrase.get():
            phrase_text = self.recovery_input.get(1.0, tk.END).strip()
            if not phrase_text:
                messagebox.showerror("Diophantine",
                    "Please enter the recovery phrase.")
                return None
            words = phrase_text.split()
            if not validate_recovery_phrase(words):
                messagebox.showerror("Diophantine",
                    "Invalid recovery phrase.")
                return None
            return phrase_text

        password_text = self.password.get()

        if self.use_keyfile.get() and self.current_keyfile:
            if not validate_keyfile(self.current_keyfile):
                messagebox.showerror("Error",
                    "Keyfile is invalid or corrupted.")
                return None
            if password_text:
                return combine_keyfile_and_password(
                    self.current_keyfile, password_text)
            else:
                keyfile_data = load_keyfile(self.current_keyfile)
                return hashlib.sha256(keyfile_data).hexdigest()

        if not password_text:
            messagebox.showerror("Diophantine",
                "Please enter a password.")
            return None
        return password_text

    # ── Decrypt Execution ────────────────────────────────────────

    def decrypt(self):
        if not self.items:
            messagebox.showerror("Diophantine",
                "No encrypted files selected.")
            return

        password = self._resolve_password()
        if password is None:
            return

        # Check for mount-only mode (VeraCrypt)
        if self.veracrypt_mode.get() == "mount":
            vc_files = [f for f in self.items
                        if self._get_effective_type(f) == "veracrypt"]
            if vc_files:
                if len(vc_files) > 1:
                    messagebox.showwarning("Diophantine",
                        "Mount mode only supports one VeraCrypt file at a time.\n"
                        "Only the first file will be mounted.")
                self._mount_veracrypt(vc_files[0], password)
                return

        # Get or prompt for output directory
        output_dir = self.output_dir.get()
        if not output_dir:
            output_dir = filedialog.askdirectory(
                title="Select output directory")
            if not output_dir:
                return
            self.output_dir.set(output_dir)

        # Reset progress
        self.app.progress["value"] = 0
        self.app.progress["maximum"] = len(self.items)
        self.root.update_idletasks()

        results = []  # (filename, "OK" or error_message)

        for i, file_path in enumerate(self.items):
            effective_type = self._get_effective_type(file_path)
            filename = os.path.basename(file_path)

            try:
                if effective_type == "zip":
                    self._decrypt_zip(file_path, output_dir, password)
                elif effective_type == "7z":
                    self._decrypt_7z(file_path, output_dir, password)
                elif effective_type == "gpg":
                    self._decrypt_gpg(file_path, output_dir, password)
                elif effective_type == "veracrypt":
                    self._extract_veracrypt(file_path, output_dir, password)
                else:
                    results.append((filename, "Unknown file type"))
                    continue

                results.append((filename, "OK"))
            except Exception as e:
                results.append((filename, str(e)))

            self.app.progress["value"] = i + 1
            self.root.update_idletasks()

        # Show summary
        ok_count = sum(1 for _, status in results if status == "OK")
        fail_count = len(results) - ok_count

        if fail_count == 0:
            messagebox.showinfo("Diophantine",
                f"Decryption complete.\n{ok_count} file(s) decrypted successfully.")
        else:
            details = "\n".join(
                f"  {name}: {status}"
                for name, status in results if status != "OK")
            messagebox.showwarning("Diophantine",
                f"Successful: {ok_count}, Failed: {fail_count}\n\n"
                f"Failed files:\n{details}")

    def _decrypt_zip(self, file_path, output_dir, password):
        def on_progress(percent):
            self.root.update_idletasks()
        extract_encrypted_zip(file_path, output_dir, password,
            progress_callback=on_progress)

    def _decrypt_7z(self, file_path, output_dir, password):
        def on_progress(percent):
            self.root.update_idletasks()
        extract_encrypted_7z(file_path, output_dir, password,
            progress_callback=on_progress)

    def _decrypt_gpg(self, file_path, output_dir, password):
        def on_progress(percent):
            self.root.update_idletasks()
        extract_gpg_encrypted(file_path, output_dir, password,
            progress_callback=on_progress)

    def _mount_veracrypt(self, file_path, password):
        mount_dir = filedialog.askdirectory(
            title="Select mount point")
        if not mount_dir:
            return
        try:
            mount_veracrypt_container(file_path, mount_dir, password)
            self.current_mount = mount_dir
            self.unmount_btn.pack(side=tk.RIGHT, padx=3, pady=8)
            messagebox.showinfo("Diophantine",
                f"Container mounted at:\n{mount_dir}\n\n"
                "Use the Unmount button when done.")
        except Exception as e:
            messagebox.showerror("Diophantine",
                f"Mount failed:\n{str(e)}")

    def _extract_veracrypt(self, file_path, output_dir, password):
        def on_progress(percent):
            self.root.update_idletasks()
        extract_veracrypt_container(file_path, output_dir, password,
            progress_callback=on_progress)
