# Cloud IAM Abuse

## Objective
Abuse cloud identity and control-plane permissions for expansion.

## Enter when
The target path is account, role, principal, or metadata driven.

## Prioritize evidence
- active principals
- assumed roles
- token scope
- metadata access
- policy gaps

## Low-noise path first
Use native control-plane evidence before broad cloud enumeration.

## Typical skills/tools
- `cloud-iam-abuse`
- cloud CLIs / targeted API calls

## Exit when
You have escalated permissions, obtained durable access, or ruled out the cloud path.
