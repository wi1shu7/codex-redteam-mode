# Privilege Escalation

## Objective
Move from the current security context to a stronger one.

## Enter when
You have code execution but insufficient rights.

## Prioritize evidence
- token privileges
- service/task misconfig
- writable paths
- kernel/app-specific weaknesses

## Low-noise path first
Prefer local configuration abuse over crash-prone or noisy exploitation.

## Typical skills/tools
- `windows-privilege-escalation`
- `linux-privilege-escalation`

## Exit when
You hold the required privilege level for the next objective.
