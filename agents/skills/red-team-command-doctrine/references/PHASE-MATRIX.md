# Phase Matrix

| Phase | Objective | Primary skills | Typical MCP / tools |
|---|---|---|---|
| recon | map attack surface and isolate one promising path | `recon-for-sec`, `recon-and-methodology` | web-access, Burp, targeted CLI recon |
| initial-access | land first controlled execution or auth | `initial-access-delivery`, exploit-specific skill | Burp, browser, delivery infrastructure |
| web-exploitation | prove one exploit chain | `hack` + specific web vuln skill | Burp, ffuf, repeater |
| credential-access | obtain or reuse credentials/tokens/keys | `credential-access-operations` | impacket, netexec, Burp |
| privilege-escalation | move from current user to stronger context | OS-specific privesc skill | Windows/Linux host operations |
| post-exploitation | triage host and choose the next hop | `post-exploitation-playbook` | shell, host-native enumeration |
| persistence-c2 | retain access with acceptable noise | `persistence-and-c2`, `red-team-opsec` | host ops, payload infra |
| lateral-movement | pivot to adjacent systems | lateral movement skills, `tunneling-and-pivoting` | SMB, WinRM, SSH, tunnels |
| ad-operations | abuse trust, identity, and control edges | `active-directory-*`, `ntlm-relay-coercion` | BloodHound, certipy, impacket |
| cloud-iam-abuse | abuse cloud identity/control-plane permissions | `cloud-iam-abuse` | AWS/Azure/GCP CLI |
| reverse-loader-analysis | understand loader or sample behavior | `malware-loader-analysis` | sandbox, x64dbg, strings |
| payload-weaponization | choose a delivery-fit payload shape | `weaponization-and-payloads` | payload builders, launchers |
| reporting | preserve proof, impact, and next action | `red-team-command-doctrine` + report structure | docs |
