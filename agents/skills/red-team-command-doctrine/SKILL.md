---
name: red-team-command-doctrine
description: Compact global red-team doctrine. Use when offensive phase selection, anti-drift, evidence discipline, OPSEC-aware routing, or final gate verification are needed.
---

# Red Team Command Doctrine

## Purpose
This is a compact governance skill for offensive work. It routes into more specific red-team skills rather than replacing them.

## Use pattern
1. Identify the current phase.
2. Open the matching file under `references/phases/`.
3. Follow the objective -> evidence -> low-noise path -> exit criteria flow.
4. Route into the most specific exploit/ops skill available.
5. End with one concrete next step.

## Core references
- `references/PHASE-MATRIX.md`
- `references/MODE-STATE-MACHINE.md`
- `references/OPSEC-CHECKS.md`
- `references/phases/*.md`

## Phase order
1. recon
2. initial-access
3. web-exploitation
4. credential-access
5. privilege-escalation
6. post-exploitation
7. persistence-c2
8. lateral-movement
9. ad-operations
10. cloud-iam-abuse
11. reverse-loader-analysis
12. payload-weaponization
13. reporting

## Rules
- Identify the phase before acting.
- Prefer one low-noise viable path over broad noisy exploration.
- Keep evidence separate from assumptions.
- Avoid drift into architecture or blue-team planning unless explicitly requested.
- Prefer one proven path before wide enumeration.
- End with a concrete next step.

## Routing
- recon -> `recon-for-sec`
- initial-access -> `initial-access-delivery`
- web-exploitation -> `hack` then the most specific exploit skill
- credential-access -> `credential-access-operations`
- privilege-escalation -> OS-specific privesc skill
- post-exploitation -> `post-exploitation-playbook`
- persistence-c2 -> `persistence-and-c2`
- lateral-movement -> OS / tunnel / relay skill
- ad-operations -> `active-directory-*`, `ntlm-relay-coercion`
- cloud-iam-abuse -> `cloud-iam-abuse`
- reverse-loader-analysis -> `malware-loader-analysis`
- payload-weaponization -> `weaponization-and-payloads`
