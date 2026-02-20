# Diophantine

Local desktop app for file encryption and decryption using existing, audited tools.

Diophantine is a Python/Tkinter GUI that orchestrates:
- `7z` for ZIP/7z encryption
- `gpg` for symmetric GPG encryption
- `veracrypt` for encrypted containers

No cloud services, no accounts, no telemetry.

## Screenshot
https://private-user-images.githubusercontent.com/145684973/550004107-671544de-7b16-41d9-b5b9-21cc61475e4a.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NzE1NTEzMzksIm5iZiI6MTc3MTU1MTAzOSwicGF0aCI6Ii8xNDU2ODQ5NzMvNTUwMDA0MTA3LTY3MTU0NGRlLTdiMTYtNDFkOS1iNWI5LTIxY2M2MTQ3NWU0YS5wbmc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjYwMjIwJTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI2MDIyMFQwMTMwMzlaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT00NjRmZTMyMTZlZjdiODFkMjkwMTVhOWJhYzAzODc4YTRlMmYyOGUwNzE2NTM0MWY5M2FmMDk3ZTFmZTM1ZWI0JlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.MygNnbhHRJxC0rJ99iWZGjNFbxZ3kKcMMrJrWJ6UNgA

## Features

- Encrypt with ZIP (AES-256), 7z (AES-256 + header encryption), GPG symmetric (AES-256), VeraCrypt container
- Decrypt with auto type detection (`.zip`, `.7z`, `.gpg/.pgp/.asc`, `.hc/.tc`)
- Batch operations and drag-and-drop support
- Password generator and entropy meter
- Optional advanced auth modes: recovery phrase, keyfile, keyfile + password
- Profiles for saving encryption settings
- Light/dark support on macOS and themed cross-platform UI

## Requirements

- Python 3.10+
- `tkinter` (usually included with Python desktop installs)
- Python package:
  - `tkinterdnd2>=0.3.0`

System tools:
- Required for core archive encryption/decryption: `7z` or `7zz`
- Optional: `gpg`
- Optional: `veracrypt`

## Install

```bash
git clone https://github.com/tsevis/diophantine.git
cd diophantine
pip install -r requirements.txt
```

### Tool installation examples

macOS (Homebrew):
```bash
brew install p7zip
brew install gnupg
# veracrypt installed manually from veracrypt.fr
```

Ubuntu/Debian:
```bash
sudo apt update
sudo apt install p7zip-full gnupg python3-tk
```

Fedora:
```bash
sudo dnf install p7zip p7zip-plugins gnupg2 python3-tkinter
```

## Run

```bash
cd src
python main.py
```

## Quick Usage

1. Open `Encrypt` tab.
2. Add files/folders.
3. Choose method and naming scheme.
4. Enter password (or advanced auth mode).
5. Encrypt to output folder.

For decryption:
1. Open `Decrypt` tab.
2. Add encrypted files.
3. Confirm/override detected type.
4. Enter matching auth input.
5. Decrypt to output folder.

Full user guide: [`MANUAL.md`](MANUAL.md)

## Security Notes

- Diophantine does not implement custom crypto; it shells out to external tools.
- Security depends on endpoint integrity and password strength.
- Keep `7z/gpg/veracrypt` updated.
- Verify encrypted output before deleting plaintext originals.

Additional docs:
- [`docs/SECURITY.md`](docs/SECURITY.md)
- [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md)
- [`docs/PHILOSOPHY.md`](docs/PHILOSOPHY.md)

## License

MIT (see [`LICENSE`](LICENSE)).
