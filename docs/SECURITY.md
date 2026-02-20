# Security Model

This document describes the security architecture, threat model, and operational security considerations for Diophantine.

## Table of Contents

1. [Overview](#overview)
2. [Encryption Standards](#encryption-standards)
3. [Security Architecture](#security-architecture)
4. [Threat Model](#threat-model)
5. [Operational Security](#operational-security)
6. [Known Limitations](#known-limitations)
7. [Security Best Practices](#security-best-practices)
8. [Incident Response](#incident-response)
9. [Reporting Security Issues](#reporting-security-issues)

---

## Overview

Diophantine is a privacy-focused tool that leverages industry-standard encryption utilities to protect sensitive data. The core philosophy is to rely exclusively on well-audited, battle-tested encryption tools rather than implementing custom cryptographic solutions.

### Design Principles

- **No custom cryptography**: All encryption is delegated to established tools with proven security records
- **Defense in depth**: Multiple layers of protection through combined use of different encryption methods
- **Minimal attack surface**: Simple architecture that orchestrates existing tools rather than reimplementing them
- **Transparency**: All operations and security assumptions are documented

---

## Encryption Standards

### Primary Encryption Methods

| Method | Algorithm | Implementation | Key Length | Mode |
|--------|-----------|----------------|------------|------|
| ZIP Archives | AES-256 | 7-Zip | 256-bit | CBC |
| Container Files | AES-256 | VeraCrypt | 256-bit | XTS |
| Hash Functions | SHA-512 | VeraCrypt | 512-bit | - |

### ZIP Encryption (7-Zip)

- **Algorithm**: AES-256 in CBC mode
- **Key derivation**: PBKDF2 with SHA-256
- **Iterations**: Configurable (default: 256,000+)
- **Use case**: Portable encrypted archives for file storage and transfer

### Container Encryption (VeraCrypt)

- **Algorithm**: AES-256 in XTS mode
- **Key derivation**: PBKDF2 with SHA-512
- **Iterations**: 500,000+ for system partitions, 200,000+ for standard volumes
- **Plausible deniability**: Hidden volume support (when configured)
- **Use case**: Persistent encrypted storage containers

### Why These Tools?

1. **7-Zip**: Open-source, widely audited, cross-platform compatibility
2. **VeraCrypt**: Successor to TrueCrypt, regularly audited, government-grade encryption

---

## Security Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Diophantine Core                      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   7-Zip     │    │ VeraCrypt   │    │   Other     │  │
│  │  (AES-256)  │    │ (AES-256)   │    │   Tools     │  │
│  └─────────────┘    └─────────────┘    └─────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │    Encrypted Output     │
              │  (ZIP / Container)      │
              └─────────────────────────┘
```

### Trust Boundaries

1. **Trusted**: User, encryption tools (7-Zip, VeraCrypt)
2. **Untrusted**: Cloud storage providers, network infrastructure, physical device access (when encrypted)
3. **Assumed Honest**: Operating system (when not compromised)

### Key Management

- Keys are derived from user-provided passwords
- No keys are stored persistently by Diophantine
- Password entropy directly determines security strength
- Users are responsible for secure password storage

---

## Threat Model

### Assets Protected

- Sensitive files and documents
- Personal data stored in containers
- Archived information in encrypted ZIPs

### Threat Actors

| Threat Actor | Capability | Protection Level |
|--------------|------------|------------------|
| Casual user | Basic computer skills | ✓ Full protection |
| Curious family/coworker | Physical access to device | ✓ Full protection |
| Cloud provider | Access to stored files | ✓ Full protection |
| Network attacker | Intercepted transfers | ✓ Full protection |
| Law enforcement | Legal coercion | △ Partial (depends on configuration) |
| Nation-state | Advanced persistent threat | ✗ Limited protection |
| Malware | OS-level compromise | ✗ No protection |

### Attack Vectors Addressed

- ✓ Unauthorized physical access to device
- ✓ Unauthorized access to cloud storage accounts
- ✓ Interception of files during transfer
- ✓ Casual inspection of device contents
- ✓ Data recovery from deleted files (when properly encrypted)

### Attack Vectors NOT Addressed

- ✗ Compromised operating system
- ✗ Hardware keyloggers
- ✗ Malware/spyware on host system
- ✗ Side-channel attacks
- ✗ Cold boot attacks
- ✗ Forensic analysis with unlimited time/resources

---

## Operational Security

### Password Requirements

For adequate security, passwords should:

- Be at least 16 characters long
- Include uppercase, lowercase, numbers, and symbols
- Have at least 64 bits of entropy
- Never be reused across different containers/archives
- Be stored in a secure password manager

### Recommended Practices

1. **Use strong, unique passwords** for each encrypted item
2. **Enable hidden volumes** in VeraCrypt when plausible deniability is needed
3. **Wipe original files** securely after encryption (use secure delete)
4. **Verify encryption** by attempting to open encrypted files
5. **Keep tools updated** (7-Zip, VeraCrypt, OS)
6. **Use full disk encryption** as an additional layer
7. **Maintain backups** of encrypted containers in separate locations

### Secure Deletion

After encrypting sensitive files:

1. Verify the encrypted archive/container opens correctly
2. Use secure deletion tools to remove originals:
   - macOS: `srm` command or third-party tools
   - Consider SSD limitations with secure delete

---

## Known Limitations

### Technical Limitations

1. **Password-based encryption**: Security is only as strong as the password
2. **No forward secrecy**: Compromised password exposes all past and future data
3. **Metadata exposure**: File names, sizes, and timestamps may be visible (ZIP)
4. **SSD wear leveling**: Secure deletion may not work reliably on SSDs
5. **RAM residues**: Encryption keys in memory may be recoverable (cold boot)

### Operational Limitations

1. **User error**: Weak passwords, password reuse, or accidental exposure
2. **Social engineering**: Coercion or deception to obtain passwords
3. **Legal compulsion**: Court orders may force password disclosure
4. **Tool vulnerabilities**: Undiscovered flaws in 7-Zip or VeraCrypt

---

## Security Best Practices

### Before Encryption

- [ ] Verify file contents are complete and correct
- [ ] Close any applications using the files
- [ ] Ensure no temporary copies exist
- [ ] Choose an appropriate password

### During Encryption

- [ ] Work in a private environment
- [ ] Ensure no malware is running
- [ ] Use a secure network if applicable

### After Encryption

- [ ] Verify the encrypted file opens with the password
- [ ] Securely delete original unencrypted files
- [ ] Clear clipboard if password was copied
- [ ] Log out of password manager if used
- [ ] Verify no temporary files remain

### Long-term Storage

- [ ] Store passwords in a secure password manager
- [ ] Maintain multiple backups of encrypted containers
- [ ] Periodically verify backup integrity
- [ ] Consider password rotation for long-term secrets
- [ ] Document recovery procedures for trusted parties

---

## Incident Response

### If You Suspect Compromise

1. **Immediately change passwords** for affected containers
2. **Re-encrypt data** with new passwords
3. **Scan for malware** on all potentially affected devices
4. **Review access logs** if available
5. **Assess scope** of potential data exposure

### If Password Is Lost

- Data recovery is **not possible** without the password
- This is by design—there is no backdoor
- Check password manager backups
- Review any documented password hints

### If Device Is Compromised

1. Assume all data on the device is exposed
2. Change all passwords from a clean device
3. Re-encrypt all sensitive data
4. Consider the device untrustworthy until cleaned

---

## Reporting Security Issues

### Vulnerability Disclosure

If you discover a security vulnerability in Diophantine:

1. **Do not** disclose publicly until the issue is resolved
2. Contact the maintainers through secure channels
3. Provide detailed reproduction steps
4. Allow reasonable time for patching before disclosure

### Contact

For security-related inquiries, please refer to the project's contact information in the main README or repository settings.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-16 | Initial comprehensive security documentation |

---

## Additional Resources

- [VeraCrypt Documentation](https://veracrypt.fr/en/Documentation.html)
- [7-Zip Security Information](https://www.7-zip.org/)
- [NIST Encryption Guidelines](https://csrc.nist.gov/projects/cryptographic-standards-and-guidelines)
- [EFF Surveillance Self-Defense](https://ssd.eff.org/)

---

*Last updated: February 16, 2026*