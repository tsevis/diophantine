# Diophantine

**Encryption & compression companion — inspired by Diophantus of Alexandria**

Diophantine is a desktop application for encrypting and compressing files using industry-standard tools. No cloud, no accounts, no noise — just local encryption under your full control.

Named after [Diophantus of Alexandria](https://en.wikipedia.org/wiki/Diophantus), the father of algebra, whose work on equations and number theory laid the foundations for modern cryptography.

---

## Features

- **Multiple encryption methods** — ZIP (AES-256), 7z (AES-256 with header encryption), GPG (AES-256 symmetric), and VeraCrypt containers
- **Batch encryption & decryption** — Process multiple files at once with automatic type detection
- **Password generator** — Built-in generator with configurable length and character sets
- **Password strength meter** — Real-time entropy calculation with strength feedback
- **Encryption profiles** — Save and load your preferred settings (3 built-in profiles included)
- **Recovery phrases** — BIP-39 mnemonic phrases for account recovery
- **Keyfile authentication** — Two-factor support with keyfile + password
- **Flexible naming** — Original, numeric, or chronological naming schemes
- **Drag and drop** — Drop files directly into the app with visual feedback
- **Light / Dark mode** — Follows macOS system appearance with manual toggle
- **Native look** — Uses macOS aqua theme for a native feel
- **Preferences** — Configurable defaults for output directory, encryption method, and naming

---

## Requirements

### Python

- **Python 3.10 or later** (tested with 3.12)
- **tkinter** — included with Python on macOS and Windows; may require a separate install on Linux

### System Tools

Diophantine relies on external encryption tools. Install the ones you plan to use:

| Tool | Used for | Required? |
|------|----------|-----------|
| **7-Zip** (p7zip) | ZIP AES-256, 7z AES-256 | Yes (core feature) |
| **GnuPG** | GPG symmetric AES-256 | Optional |
| **VeraCrypt** | Encrypted containers | Optional |

---

## Installation

### macOS

**1. Install Python dependencies:**

```bash
pip install -r requirements.txt
```

**2. Install system tools:**

```bash
# 7-Zip (required)
brew install p7zip

# GnuPG (optional, for GPG encryption)
brew install gnupg

# VeraCrypt (optional, for encrypted containers)
# Download from https://veracrypt.fr/en/Downloads.html
# After installing, create a symlink for CLI access:
sudo ln -s /Applications/VeraCrypt.app/Contents/MacOS/VeraCrypt /usr/local/bin/veracrypt
```

**3. Run the app:**

```bash
cd src
python main.py
```

---

### Windows

**1. Install Python:**

Download Python 3.10+ from [python.org](https://www.python.org/downloads/). During installation, check **"Add Python to PATH"** and ensure **tkinter** is selected (it is by default).

**2. Install Python dependencies:**

```powershell
pip install -r requirements.txt
```

**3. Install system tools:**

- **7-Zip**: Download from [7-zip.org](https://www.7-zip.org/) and add to your system PATH
- **GnuPG** (optional): Download Gpg4win from [gpg4win.org](https://gpg4win.org/)
- **VeraCrypt** (optional): Download from [veracrypt.fr](https://veracrypt.fr/en/Downloads.html)

**4. Run the app:**

```powershell
cd src
python main.py
```

---

### Linux (Ubuntu / Debian)

**1. Install Python and tkinter:**

```bash
sudo apt update
sudo apt install python3 python3-pip python3-tk
```

**2. Install Python dependencies:**

```bash
pip3 install -r requirements.txt
```

**3. Install system tools:**

```bash
# 7-Zip (required)
sudo apt install p7zip-full

# GnuPG (optional — usually pre-installed)
sudo apt install gnupg

# VeraCrypt (optional)
# Download the .deb package from https://veracrypt.fr/en/Downloads.html
# Then install:
sudo dpkg -i veracrypt-*.deb
```

**4. Run the app:**

```bash
cd src
python3 main.py
```

---

### Linux (Fedora / RHEL)

**1. Install Python and tkinter:**

```bash
sudo dnf install python3 python3-pip python3-tkinter
```

**2. Install Python dependencies:**

```bash
pip3 install -r requirements.txt
```

**3. Install system tools:**

```bash
# 7-Zip (required)
sudo dnf install p7zip p7zip-plugins

# GnuPG (optional — usually pre-installed)
sudo dnf install gnupg2

# VeraCrypt (optional)
# Download the .rpm package from https://veracrypt.fr/en/Downloads.html
sudo rpm -i veracrypt-*.rpm
```

**4. Run the app:**

```bash
cd src
python3 main.py
```

---

### Linux (Arch)

```bash
sudo pacman -S python python-pip tk p7zip gnupg
pip install -r requirements.txt
cd src
python main.py
```

---

## Usage

### Encrypting Files

1. Open the **Encrypt** tab
2. Add files using the **Add Files** / **Add Folder** buttons or drag and drop
3. Choose an encryption method (ZIP, 7z, GPG, or VeraCrypt)
4. Choose a naming scheme (Original, Numeric, or Chronological)
5. Enter a password (or use the **Generate** button)
6. Click **Encrypt** and select an output directory

### Decrypting Files

1. Open the **Decrypt** tab
2. Add encrypted files using **Add Files** or drag and drop
3. The file type is auto-detected (or select manually via the Override dropdown)
4. Enter the password used during encryption
5. Click **Decrypt** and select an output directory

### Profiles

Use profiles to save your preferred encryption settings:

- **Quick Share** — ZIP, single archive, original names. Best for sharing files.
- **Maximum Security** — 7z with header encryption, numeric names, two-factor ready.
- **Daily Backup** — GPG, chronological names, single archive. Ideal for routine backups.

Select a profile from the dropdown in the Encrypt tab. You can also create your own with the **Save** button.

### Advanced Features

Enable **Advanced Features** in the Encrypt tab to access:

- **Recovery phrases** — Generate a BIP-39 mnemonic for password recovery
- **Keyfile authentication** — Generate or select a `.diophantus` keyfile
- **Two-factor mode** — Require both a keyfile and a password for encryption

### Light / Dark Mode

On macOS, click the **Dark Mode** / **Light Mode** button in the top bar to toggle appearance. The app also follows the system appearance automatically.

---

## Project Structure

```
diophantine/
  config/                    # App configuration (auto-created)
    preferences.json         # User preferences
    profiles/                # Saved encryption profiles
  docs/
    PHILOSOPHY.md
    SECURITY.md
    THREAT_MODEL.md
  src/
    main.py                  # Entry point
    crypto/
      gpg_engine.py          # GPG symmetric encryption
      sevenz_engine.py       # 7z AES-256 encryption
      veracrypt_engine.py    # VeraCrypt container operations
      zip_engine.py          # ZIP AES-256 encryption
    ui/
      main_window.py         # Main window shell and theme
      encrypt_tab.py         # Encrypt tab UI and logic
      decrypt_tab.py         # Decrypt tab UI and logic
      password_generator.py  # Password generator dialog
      preferences_window.py  # Preferences dialog
      theme.py               # Dark mode detection and color palettes
    utils/
      entropy.py             # Password entropy calculation
      keyfile_auth.py        # Keyfile generation and validation
      metron.py              # Password strength scoring
      naming.py              # File naming schemes
      preferences.py         # Preferences load/save
      profiles.py            # Profile management
      recovery_phrase.py     # BIP-39 mnemonic phrases
  requirements.txt
  README.md
```

---

## Security Model

Diophantine does **not** implement any custom cryptography. All encryption is delegated to established, audited tools:

| Method | Tool | Algorithm | Notes |
|--------|------|-----------|-------|
| ZIP | 7-Zip | AES-256 | Widely compatible |
| 7z | 7-Zip | AES-256 | Header encryption hides filenames |
| GPG | GnuPG | AES-256 | Password via stdin (never on command line) |
| VeraCrypt | VeraCrypt | AES / SHA-512 | Full-disk encryption containers |

### What Diophantine protects against

- Casual access to your files
- Lost or stolen devices
- Untrusted cloud storage

### What it does NOT protect against

- A compromised operating system
- Keyloggers or screen capture malware
- Weak or reused passwords

For more details, see [docs/SECURITY.md](docs/SECURITY.md) and [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md).

---

## License

This project is licensed under the [MIT License](LICENSE).

---

*Encryption is not secrecy. It is structure applied to uncertainty.*
# diophantine
Encryption &amp; compression companion — inspired by Diophantus of Alexandria
