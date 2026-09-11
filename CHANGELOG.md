# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Security
- Passwords no longer appear in any tool's command line. 7z and ZIP receive
  them through a private terminal prompt, GPG and VeraCrypt through stdin.
- A recovery phrase is now stretched with PBKDF2-HMAC-SHA512 before it is
  handed to an encryption tool, instead of being passed verbatim and relying
  on each backend's own key derivation. Archives written with the older
  scheme still open: decryption tries the derived secret first and falls
  back to the bare phrase.
- Decryption stages its output and refuses to overwrite existing files, and
  archive members that are absolute, traverse upward, or are not regular
  files are rejected before extraction.
- Keyfiles, profiles and preferences are created owner-only rather than
  relying on the umask.

### Fixed
- 7z and ZIP operations no longer freeze the app. The password was written
  before 7-Zip disabled terminal echo, and its `TCSAFLUSH` discarded it.
- Multi-file GPG bundles (`.tar.gpg`) decrypt again.
- The progress bar advances during 7z and ZIP work instead of sitting at 0%.

### Added
- `MANUAL.md` with full user operations guide.
- `CHANGELOG.md` for release tracking.
- A test suite, with `pyproject.toml` carrying the ruff, pytest and coverage
  configuration and a `gui` marker that keeps window-opening tests opt-in.

### Changed
- Rewrote `README.md` to align with current implemented behavior.
- Kept existing screenshot reference in README, as requested.
- Clarified dependencies and external-tool requirements.
- `unmount_veracrypt_container` now requires the mount point to unmount.

### Removed
- `src/utils/metron.py`, an unused second password-strength scorer that
  disagreed with the one the UI actually uses.

## [0.1.0] - 2026-02-20

### Added
- Tkinter desktop UI with Encrypt/Decrypt tabs.
- Encryption workflows for ZIP, 7z, GPG symmetric, and VeraCrypt containers.
- Batch file operations and drag-and-drop support.
- Password generator and entropy-based strength meter.
- Advanced auth options (recovery phrase, keyfile, keyfile + password).
- Profile management and preferences persistence.
- Security, threat model, and philosophy docs under `docs/`.
