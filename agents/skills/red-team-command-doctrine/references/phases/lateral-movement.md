# Lateral Movement

## Objective
Pivot from the current node to the next valuable node.

## Enter when
Current access reveals adjacent systems or trusted paths.

## Prioritize evidence
- reachable systems
- admin/session relationships
- token/cred applicability
- protocol fit

## Low-noise path first
Prefer one validated pivot path over mass auth attempts.

## Typical skills/tools
- `windows-lateral-movement`, `linux-lateral-movement`
- `tunneling-and-pivoting`

## Exit when
You have landed on the higher-value node or rejected the pivot path.
