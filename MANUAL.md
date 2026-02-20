# Diophantine Manual

## 1. Purpose

Diophantine is a local desktop GUI for encrypting and decrypting files with external tools (`7z`, `gpg`, `veracrypt`).

## 2. Prerequisites

- Python 3.10+
- `tkinter`
- `tkinterdnd2` (`pip install -r requirements.txt`)
- External tools (depending on workflow):
  - `7z` or `7zz` (recommended/required for ZIP and 7z workflows)
  - `gpg` (for GPG workflows)
  - `veracrypt` (for container workflows)

## 3. Start the Application

```bash
cd src
python main.py
```

## 4. Main Interface

- `Encrypt` tab: create encrypted output
- `Decrypt` tab: decrypt or mount encrypted input
- Top bar: `Preferences`
- Bottom bar: shared progress indicator

## 5. Encrypt Tab

### 5.1 Add Input

- `Add Files`
- `Add Folder`
- Drag and drop files/folders

### 5.2 Basic Options

- `Create single archive`
- Encryption method:
  - `ZIP (AES-256)`
  - `7z (AES-256)`
  - `GPG (AES-256)`
  - `VeraCrypt Container`
- Naming scheme:
  - `Original Name`
  - `Numeric`
  - `Chronological`

### 5.3 Password and Strength

- Enter password manually, or use `Generate`
- Entropy meter updates while typing
- Low-entropy passwords trigger a warning before encryption

### 5.4 Advanced Features

Enable `Enable Advanced Features` to use:
- Recovery phrase generation (BIP-39 style phrase)
- Keyfile generation/selection (`.diophantus`)
- Two-factor mode (keyfile + password)

### 5.5 Profiles

Use profile controls to save and load settings:
- `Save` current settings
- Select from profile dropdown
- `Delete` selected profile

Profiles are stored in `config/profiles/*.json`.

### 5.6 Output Behavior

- ZIP/7z/GPG single archive mode uses default output names:
  - `diophantine.zip`
  - `diophantine.7z`
  - `diophantine.tar.gpg`
- Non-single mode outputs one encrypted file per input item.
- VeraCrypt mode creates `diophantine.hc`.

## 6. Decrypt Tab

### 6.1 Add Input

- `Add Files`
- Drag and drop encrypted files

Supported extensions include:
- ZIP: `.zip`
- 7z: `.7z`
- GPG: `.gpg`, `.pgp`, `.asc`, `.tar.gpg`
- VeraCrypt: `.hc`, `.tc`

### 6.2 File Type Handling

- Auto-detection based on extension
- Optional manual override via dropdown

### 6.3 Authentication

- Password field (default)
- Optional keyfile auth
- Optional recovery phrase auth

### 6.4 VeraCrypt Modes

When a VeraCrypt file is detected:
- `Mount + Extract + Unmount (automated)`
- `Mount only (manual access)`

`Mount only` supports one container at a time.

### 6.5 Decrypt Flow

1. Choose or confirm output directory
2. Click `Decrypt` (or `Mount` in mount-only mode)
3. Review completion summary

## 7. Preferences

`Preferences` window includes:
- Default output directory
- Default encryption method
- Default naming scheme

Preferences are stored in `config/preferences.json`.

## 8. Keyfile Guidance

- Keep keyfiles private and backed up
- Do not store keyfile in same place as encrypted archives when avoidable
- If two-factor mode was used for encryption, both keyfile and password are required

## 9. Recovery Phrase Guidance

- Write the phrase offline
- Keep it physically secure
- Treat it like a password equivalent

## 10. Troubleshooting

### `7-Zip is not installed`
Install `p7zip` (or ensure `7z`/`7zz` is in `PATH`).

### `GPG is not installed`
Install `gnupg` and confirm `gpg` executable is available.

### `VeraCrypt is not installed`
Install VeraCrypt and ensure CLI is callable as `veracrypt`.

### Decryption fails
- Confirm matching method and auth mode
- Verify password/keyfile/recovery phrase
- Try manual file type override

### Drag-and-drop not working
- Confirm `tkinterdnd2` is installed
- Restart app after environment changes

## 11. Security Operating Notes

- Keep OS and encryption tools updated
- Verify encrypted output opens before deleting plaintext
- For high-value data, keep redundant encrypted backups
- This app does not protect against malware on a compromised host
