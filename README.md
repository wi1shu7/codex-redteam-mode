# Codex Red Team Opt-In Mode

[English](./README.md) | [中文](./README_ZH.md)

> Defaults to normal; only enters red-team mode when explicitly enabled.

This is a lightweight, pack-first red team runtime/configuration layer for Codex.

Its goal is not to turn Codex into an automated attack platform — it provides structured, layered routing for red team workflows while keeping normal operations unaffected.

## Project Description

- This repository is a **general GitHub repository**
- It should not contain personal local paths, private target data, or user-specific tool preferences

## Why This Project?

Many "persistent red team hints" ultimately lead to two bad outcomes:

1. **Pollution of normal operations**
2. **Overly heavy injection, leading to context bloat**

This project does the opposite:

- **Normal mode remains normal**
- **Red team mode must be explicitly enabled**
- **Hooks remain lightweight**
- **Routes remain layered and restrained**

## Core Features

- Explicit opt-in for Red Team Mode
- Three modes: `normal` / `redteam-light` / `redteam-full`
- Structured JSON runtime state
- Rule-first + semantic fallback phase detection
- Session-isolated state file
- Lightweight prompt overlay
- Pack-first routing mainline:

```text
phase -> router -> pack -> leaf
```

## Coverage Scenarios

**Core Phases:**

- web
- ad (Active Directory)
- postex (Post-Exploitation)
- reverse (Reverse Engineering)
- code-audit
- payload
- evasion

**Extended Router/Pack Families:**

- recon
- api
- auth
- injection
- file
- business logic
- cloud
- container / kubernetes
- network / protocol
- crypto
- mobile

## Installation

The installer uses **managed incremental installation**:

- Preserves the user's original `AGENTS.md`
- Preserves the user's original `hooks.json`
- Injects only managed blocks from this repository
- Cleans out old-version runtime remnants from this repository
- Cleanly installs the current version
- Writes to the install manifest
- Auto-runs validation post-install

### Python

```bash
python scripts/install.py
```

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

### macOS / Linux

```bash
python3 scripts/install.py
```

## Quick Start

### Enable Red Team Mode

```text
Enter Red Team Mode
Enable Red Team Mode

/redteam on
/redteam light
/redteam full
enable red team mode
```

### Disable Red Team Mode

```text
Exit Red Team Mode
Disable Red Team Mode

/redteam off
disable red team mode
```

### Verify Installation

```bash
python scripts/validate.py
```

## Working Flow

### Runtime Mainline

The current actual routing mainline is:

```text
phase -> router -> pack -> leaf
```

`method` still exists, but is only used as a soft tip when it is genuinely helpful — it is no longer the primary routing axis.

### Mode Description

| Mode | Default | Typical Use |
|---|---:|---|
| `normal` | Yes | Coding, documentation, general research |
| `redteam-light` | No | Targeted security analysis, planning, review |
| `redteam-full` | No | More constrained red team workflow |

## Validation

The repository includes:

- Installer checks
- Routing tests
- Mode switching tests
- Orchestration gate checks
- Prompt-chain checks

Run with:

```bash
python -m unittest discover -s tests -p "test_*.py"
python scripts/validate.py
```

## Known Limitations

- This is the control/configuration layer, not a complete attack platform
- The actual effect of the prompt overlay still depends on the target Codex environment
- The user's local private prompt system may differ from the repository version
- The actual execution depth still depends on your MCP / Tools

## ⚠️ Disclaimer

**This project is intended solely for authorized penetration testing, red team research, and defensive security experiments.**

- Use only on systems or environments where you have **explicit authorization**
- Unauthorized use on third-party or production systems is **prohibited**
- The authors and contributors **assume no responsibility** for misuse, legal consequences, service interruption, or data loss
- By using this project, you agree to assume **all risks** and ensure that your actions comply with applicable laws and regulations

## Contributions & Acknowledgements

### Individual Contributors

- **Mingxi** (Mister Security Team) — suggested adding semantic judgment, removing methodology, and subdividing skills for smarter AI behavior during work phases. X: [@xishan12509850](https://x.com/xishan12509850)
- **Nirvana** — suggested workflow optimization and overlay installation enablement. X: [@Nirvana_543](https://x.com/Nirvana_543)
- **PINGS** — suggestions for enhancing jailbreak text

### Reference Projects

Special thanks to the following projects for providing method layer, technology routing layer, and skill pack structure references:

- [qiushi-skill](https://github.com/qiushi-L/qiushi-skill)
- [yaklang/hack-skills](https://github.com/yaklang/hack-skills)
- [mukul975/Anthropic-Cybersecurity-Skills](https://github.com/mukul975/Anthropic-Cybersecurity-Skills)

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for contribution guidelines.

## License

MIT, see [LICENSE](./LICENSE).
