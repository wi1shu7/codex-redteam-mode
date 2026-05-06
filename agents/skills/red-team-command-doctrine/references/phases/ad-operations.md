# AD Operations

## Objective
Abuse trust, identity, sessions, and control edges inside AD.

## Enter when
The target path is domain-centric.

## Prioritize evidence
- sessions
- ACL edges
- delegation
- ADCS exposure
- relay/coercion fit

## Low-noise path first
Use graph/evidence-driven progression instead of broad domain-wide noise.

## Typical skills/tools
- `active-directory-acl-abuse`
- `active-directory-kerberos-attacks`
- `active-directory-certificate-services`
- `ntlm-relay-coercion`

## Exit when
You gain the target identity/control edge or determine the domain path should shift.
