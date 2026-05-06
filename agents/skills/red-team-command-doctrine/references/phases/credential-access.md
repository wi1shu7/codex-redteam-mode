# Credential Access

## Objective
Obtain, replay, or validate credentials, tokens, tickets, or keys.

## Enter when
A foothold or reachable auth surface exists.

## Prioritize evidence
- stored secrets
- token/cookie/session reuse
- delegated creds
- key material

## Low-noise path first
Start with existing local evidence before sprays or broad auth attempts.

## Typical skills/tools
- `credential-access-operations`
- AD/host/Burp tooling

## Exit when
You have stronger identity material or have ruled out the local credential path.
