from __future__ import annotations

import re
from typing import Optional

from .semantic_phase import classify_phase_semantically

SEMANTIC_THRESHOLD = 0.25

SECURITY_PATTERNS = [
    ("warmup", [r"\b(osint|fingerprint|tech stack|technology stack|cms|framework version|what runs|built with)\b", "\u6280\u672f\u6808", "\u7f51\u7ad9\u6307\u7eb9", "\u7ec4\u4ef6\u8bc6\u522b"]),
    ("defense", [r"\b(waf rule|csp policy|security header|auth flow|authorization model|rbac|access control model|defense mechanism|rate limit|cors policy)\b", "\u9632\u62a4\u673a\u5236", "\u5b89\u5168\u7b56\u7565", "\u8ba4\u8bc1\u6d41\u7a0b", "\u6388\u6743\u6a21\u578b", "\u8bbf\u95ee\u63a7\u5236"]),
    ("web", [r"\b(xss|sqli|ssrf|ssti|idor|csrf|xxe|cmdi|graphql|api|swagger|openapi|burp|repeater|proxy)\b", "SQL\u6ce8\u5165", "SSRF", "XXE", "XSS", "SSTI", "\u8d8a\u6743", "\u8bf7\u6c42", "\u54cd\u5e94", "\u63a5\u53e3", "\u9274\u6743", "\u767b\u5f55"]),
    ("ad", [r"\b(kerberos|ntlm|adcs|bloodhound|acl|delegation|kerberoast|asreproast)\b", "\u57df\u63a7", "\u59d4\u6d3e", "\u7968\u636e", "\u8bc1\u4e66\u670d\u52a1", "\u57df\u5185\u6a2a\u5411"]),
    ("postex", [r"\b(post[- ]?ex|foothold|shell|privilege escalation|lateral movement|pivot)\b", "\u62ff\u5230 shell", "\u63d0\u6743", "\u6a2a\u5411", "\u843d\u5730", "\u4e3b\u673a\u5206\u8bca"]),
    ("reverse", [r"\b(reverse|reverse engineer(?:ing)?|malware|dropper|stager|loader|sample|unpack(?:ing)?|execution chain|decompile|binary)\b", "\u9006\u5411", "\u53cd\u7f16\u8bd1", "\u6837\u672c", "\u6267\u884c\u94fe", "\u8131\u58f3", "\u4e8c\u8fdb\u5236"]),
    ("code-audit", [r"\b(code audit|source code|controller|handler|middleware|grep|taint|sink|entrypoint)\b", "\u6e90\u7801", "\u5ba1\u8ba1", "\u5165\u53e3", "\u63a7\u5236\u5668", "\u4e2d\u95f4\u4ef6", "\u5371\u9669\u51fd\u6570", "\u4fe1\u4efb\u8fb9\u754c"]),
    ("payload", [r"\b(payload|shellcode|staged|stageless|launcher|beacon)\b", "\u8f7d\u8377", "\u542f\u52a8\u5668", "shellcode", "\u56de\u8fde", "\u4fe1\u6807"]),
    ("cloud", [r"\b(aws|azure|gcp|iam|sts|role assumption|cloudtrail|metadata service)\b", "AWS", "Azure", "GCP", "IAM", "\u4e91\u51ed\u8bc1", "\u5143\u6570\u636e\u670d\u52a1"]),
    ("container", [r"\b(kubernetes|k8s|helm|container|docker|pod|namespace|hostpath|privileged)\b", "K8S", "\u5bb9\u5668", "\u96c6\u7fa4", "\u9003\u9038", "Pod"]),
    ("network", [r"\b(http/2|websocket|ws|request smuggling|dns rebinding|protocol|tcp|udp|packet|pcap)\b", "\u534f\u8bae", "\u6d41\u91cf", "\u6293\u5305", "\u8bf7\u6c42\u8d70\u79c1", "WebSocket", "DNS\u91cd\u7ed1\u5b9a"]),
    ("crypto", [r"\b(rsa|aes|des|hash|sha|md5|padding oracle|lattice|cipher|stego)\b", "\u5bc6\u7801\u5b66", "\u52a0\u5bc6", "\u54c8\u5e0c", "\u4fa7\u4fe1\u9053", "\u9690\u5199"]),
    ("mobile", [r"\b(android|ios|apk|ipa|frida|objection|pinning|mobile)\b", "\u5b89\u5353", "\u82f9\u679c", "\u79fb\u52a8\u7aef", "\u8bc1\u4e66\u9501\u5b9a", "\u6293\u5305"]),
    ("evasion", [r"\b(edr|av|defender|waf|403|csp|bypass|sandbox)\b", "\u514d\u6740", "\u7ed5\u8fc7", "\u6c99\u7bb1", "\u5bf9\u6297", "WAF"]),
]


def detect_phase_rule_based(prompt: str) -> Optional[str]:
    for phase, patterns in SECURITY_PATTERNS:
        for pat in patterns:
            if re.search(pat, prompt, re.I):
                return phase
    return None


def detect_phase(prompt: str) -> str:
    matched = detect_phase_rule_based(prompt)
    if matched:
        return matched
    phase, score = classify_phase_semantically(prompt)
    if phase and score >= SEMANTIC_THRESHOLD:
        return phase
    return "general"
