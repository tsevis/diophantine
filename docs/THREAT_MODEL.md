# Threat Model

> *"The unexamined threat is not worth defending against."*

This document defines the threat model for Diophantine, specifying what the software is designed to protect, against whom, and where its limitations lie.

---

## Table of Contents

1. [Overview](#overview)
2. [Assets](#assets)
3. [Trust Assumptions](#trust-assumptions)
4. [Threat Actors](#threat-actors)
5. [Attack Vectors](#attack-vectors)
6. [Out of Scope](#out-of-scope)
7. [Risk Matrix](#risk-matrix)
8. [Mitigations](#mitigations)
9. [Residual Risks](#residual-risks)

---

## Overview

### Purpose

This threat model serves to:
- Define what Diophantine protects
- Clarify what it does **not** protect against
- Set realistic expectations for users
- Guide future security decisions

### Scope

This model applies to Diophantine's core functionality:
- ZIP archive encryption via 7-Zip (AES-256)
- Container encryption via VeraCrypt (AES-256)
- Local file operations

---

## Assets

### Primary Assets

| Asset | Description | Sensitivity |
|-------|-------------|-------------|
| **Personal Documents** | Text files, PDFs, spreadsheets, notes | High |
| **Archives** | Encrypted ZIP files containing sensitive data | High |
| **Containers** | VeraCrypt volumes with persistent data | High |
| **Passwords** | User-provided encryption credentials | Critical |
| **Metadata** | File names, sizes, timestamps (may be visible) | Medium |

### Asset Flow

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Plaintext   │ -> │  Diophantine │ -> │  Encrypted   │
│   Files      │    │   (7-Zip/    │    │   Output     │
│              │    │  VeraCrypt)  │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
     │                                       │
     │         ┌──────────────┐              │
     └────────>|  Secure      |<─────────────┘
               |  Deletion    │
               └──────────────┘
```

---

## Trust Assumptions

### Trusted Components

| Component | Reason | Risk if Compromised |
|-----------|--------|---------------------|
| **7-Zip** | Open-source, widely audited | Catastrophic |
| **VeraCrypt** | Open-source, regularly audited | Catastrophic |
| **Operating System** | Required for execution | High |
| **User** | Key holder and decision maker | N/A |
| **Hardware** | CPU, RAM, storage | Medium-High |

### Untrusted Components

| Component | Assumption |
|-----------|------------|
| **Cloud Storage Providers** | May be compromised or coerced |
| **Network Infrastructure** | Communications may be intercepted |
| **Third-party Applications** | May leak data if given access |

### Assumed Honest

- The operating system (when not infected)
- The hardware (no hardware backdoors)
- The user (acting in their own interest)

---

## Threat Actors

### Actor Classification

| Actor | Capability | Motivation | Protection Status |
|-------|------------|------------|-------------------|
| **Casual User** | Basic computer skills; file browsing | Curiosity | ✓ Protected |
| **Family/Coworker** | Physical device access; knows user | Opportunistic | ✓ Protected |
| **Cloud Provider Employee** | Access to stored files | Curiosity, policy enforcement | ✓ Protected |
| **Network Attacker** | Packet interception; MITM attacks | Data theft | ✓ Protected |
| **Data Broker** | Aggregation of leaked data | Profit | ✓ Protected |
| **Criminal Hacker** | Malware, phishing, exploits | Financial gain | △ Partial |
| **Law Enforcement** | Legal coercion; warrants | Investigation | △ Partial |
| **Nation-State** | Advanced persistent threats; zero-days | Intelligence | ✗ Not Protected |
| **Insider Threat** | Trusted person with access | Malice, coercion | △ Varies |

### Actor Details

#### ✓ Protected Against

**Casual User / Family / Coworker**
- **Scenario**: Device left unlocked; file browsing
- **Protection**: Encrypted files appear as unreadable data
- **Confidence**: High

**Cloud Provider**
- **Scenario**: Employee access; data center breach
- **Protection**: AES-256 encryption renders data useless without password
- **Confidence**: High

**Network Attacker**
- **Scenario**: Intercepting file transfers; public WiFi
- **Protection**: Encrypted files cannot be decrypted in transit
- **Confidence**: High

#### △ Partially Protected Against

**Criminal Hacker**
- **Scenario**: Malware infection; keyloggers; phishing
- **Protection**: Encrypted data at rest is safe; credentials may be compromised
- **Confidence**: Medium (depends on user behavior)

**Law Enforcement**
- **Scenario**: Legal coercion; border searches
- **Protection**: Strong encryption resists technical attacks; legal compulsion may force password disclosure
- **Confidence**: Medium (VeraCrypt hidden volumes may help)

#### ✗ Not Protected Against

**Nation-State Actors**
- **Scenario**: Targeted attacks; zero-day exploits; supply chain compromise
- **Protection**: None. If the OS or hardware is compromised, encryption cannot help.
- **Confidence**: Low

**Advanced Malware**
- **Scenario**: Rootkits; bootkits; firmware-level persistence
- **Protection**: None. Malware operating at kernel level can capture passwords and plaintext.
- **Confidence**: Low

---

## Attack Vectors

### Vectors Addressed

| Attack Vector | Description | Mitigation | Status |
|---------------|-------------|------------|--------|
| **Physical Device Access** | Thief accesses stolen laptop | AES-256 encryption | ✓ Mitigated |
| **Cloud Storage Breach** | Attacker gains cloud account access | Encrypted archives | ✓ Mitigated |
| **Network Interception** | MITM during file transfer | Encrypted payload | ✓ Mitigated |
| **File Recovery** | Recovering deleted plaintext | Secure deletion | ✓ Mitigated |
| **Casual Inspection** | Browsing visible files | Unreadable encrypted data | ✓ Mitigated |
| **Brute Force** | Password guessing attacks | 256-bit keys; PBKDF2 | ✓ Mitigated |

### Vectors NOT Addressed

| Attack Vector | Description | Why Not Addressed |
|---------------|-------------|-------------------|
| **Keyloggers** | Hardware or software key capture | Outside software scope |
| **Screen Capture** | Malware capturing display | OS-level compromise |
| **Memory Extraction** | Cold boot attacks; RAM scraping | Hardware/physical attack |
| **Side-Channel Attacks** | Timing, power analysis | Specialized attacks |
| **Social Engineering** | Tricking user into revealing password | Human factor |
| **Physical Coercion** | Torture; legal compulsion | Outside technical scope |
| **Supply Chain Attacks** | Compromised updates; fake downloads | Distribution security |
| **Zero-Day Exploits** | Unknown OS/application vulnerabilities | Unpredictable |

---

## Out of Scope

### Explicitly Out of Scope

Diophantine does **not** protect against:

1. **Endpoint Compromise**
   - Infected operating systems
   - Hardware keyloggers
   - Compromised peripherals

2. **User Behavior**
   - Weak passwords
   - Password reuse
   - Voluntary disclosure
   - Phishing victimization

3. **Physical Attacks**
   - Device seizure with compelled password disclosure
   - Hardware tampering
   - Evil maid attacks (without hidden volumes)

4. **Advanced Persistent Threats**
   - Nation-state surveillance
   - Targeted malware campaigns
   - Zero-day exploitation

### Design Philosophy

> *"Perfect security is the enemy of good security."*

Attempting to protect against all threats would:
- Add complexity (increasing attack surface)
- Reduce usability (decreasing adoption)
- Create false confidence (dangerous)

Instead, Diophantine focuses on **common, high-probability threats** where encryption provides meaningful protection.

---

## Risk Matrix

### Likelihood vs. Impact

```
                    IMPACT
              Low │ Medium │ High │ Critical
         ─────────┼────────┼──────┼──────────
    High  │        │        │      │
         │        │        │      │
Likeli-  Medium │        │   ✓  │   ✓
hood     │        │        │      │
         │        │        │      │
    Low   │        │        │      │   ✗
         │        │        │      │
         ─────────┴────────┴──────┴──────────
                  ✓ = Protected
                  ✗ = Not Protected
```

### Risk Prioritization

| Risk | Likelihood | Impact | Priority | Status |
|------|------------|--------|----------|--------|
| Lost/stolen device | Medium | High | High | ✓ Mitigated |
| Cloud account breach | Medium | High | High | ✓ Mitigated |
| Network interception | Low | Medium | Medium | ✓ Mitigated |
| Malware/keylogger | Medium | Critical | High | ✗ Out of scope |
| Nation-state target | Low | Critical | Low | ✗ Out of scope |

---

## Mitigations

### Implemented Mitigations

| Control | Type | Effectiveness |
|---------|------|---------------|
| AES-256 encryption | Technical | High |
| PBKDF2 key derivation | Technical | High |
| Secure file deletion | Technical | Medium-High |
| No password storage | Technical | High |
| Local-only operation | Architectural | High |

### Recommended User Mitigations

| Control | Type | Purpose |
|---------|------|---------|
| Strong passwords | Behavioral | Resist brute force |
| Full disk encryption | Technical | Protect when OS is off |
| Antivirus/anti-malware | Technical | Detect endpoint threats |
| Two-factor authentication | Technical | Protect cloud accounts |
| Regular backups | Operational | Recover from loss |
| Security awareness | Behavioral | Resist social engineering |

---

## Residual Risks

After all mitigations, these risks remain:

| Risk | Residual Level | Acceptable? |
|------|----------------|-------------|
| Password compromise (user error) | Medium | Yes (user education) |
| OS compromise | Low-Medium | Yes (out of scope) |
| Legal coercion | Low | Yes (unavoidable) |
| Hardware backdoors | Low | Yes (unverifiable) |
| Quantum computing (future) | Low | Yes (not yet practical) |

### Risk Acceptance

Users accept that:
1. Encryption protects **data at rest**, not **data in use**
2. Passwords are the **single point of failure**
3. **Endpoint security** is the user's responsibility
4. **Legal protections** vary by jurisdiction

---

## Assumptions and Dependencies

### Critical Assumptions

1. 7-Zip and VeraCrypt implementations are correct
2. AES-256 remains cryptographically secure
3. PBKDF2 provides adequate key stretching
4. User passwords have sufficient entropy
5. Operating system is not actively compromised

### External Dependencies

| Dependency | Purpose | Risk if Unavailable |
|------------|---------|---------------------|
| 7-Zip | ZIP encryption | Core feature loss |
| VeraCrypt | Container encryption | Core feature loss |
| OS file APIs | File operations | Application failure |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-16 | Initial comprehensive threat model |

---

## Review Schedule

This threat model should be reviewed:
- **Annually** at minimum
- **After any security incident**
- **When adding new features**
- **When threat landscape changes significantly**

---

*Last updated: February 16, 2026*