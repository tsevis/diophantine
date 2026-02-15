# Security Model

Diophantine uses only well-established encryption tools:
- ZIP: AES-256 via 7-Zip
- Containers: VeraCrypt (AES / SHA-512)

No custom cryptography is implemented.

## What Diophantine protects against
- Casual access
- Lost devices
- Untrusted cloud storage

## What it does NOT protect against
- Compromised OS
- Keyloggers
- Weak passwords