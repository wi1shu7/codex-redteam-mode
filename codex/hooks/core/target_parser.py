"""Target parser: extract domain/URL/IP from user prompts.

Detects whether user input is a bare target (domain/URL/IP with no explicit
test direction). Bare targets route to recon-intake instead of a specific
security skill.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


_DOMAIN_RE = re.compile(
    r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"
    r"[a-zA-Z]{2,63}\b"
)
_IPV4_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)
_IPV6_RE = re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}\b")
_URL_RE = re.compile(r"https?://[^\s\"'<>\]\)]+", re.IGNORECASE)
_CIDR_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)/\d{1,2}\b"
)

_DIRECTION_PATTERNS = [
    r"\b(?:xss|sqli|sql injection|ssrf|ssti|idor|csrf|xxe|rce|lfi|rfi)\b",
    r"\b(?:exploit|vulnerability|vuln|attack|bypass|inject|payload|shell)\b",
    r"\b(?:brute\s*force|privilege\s*escalation|lateral\s*movement)\b",
    r"\b(?:reverse\s*shell|web\s*shell|backdoor|trojan)\b",
    r"\b(?:pentest|penetration\s*test|red\s*team|security\s*audit)\b",
    r"\b(?:fuzzing|fuzz|scan\s*for|check\s*for|test\s*for|find)\b",
    r"\b(?:login|auth|token|session|cookie|jwt|oauth|api\s*key)\b",
    r"\b(?:upload|download|file\s*inclusion|directory\s*traversal)\b",
    r"\b(?:dns\s*rebind|request\s*smuggling|deserialization)\b",
    r"(?:注入|漏洞|攻击|绕过|提权|横向|利用|爆破|getshell|拿下|打点)",
    r"(?:测试|检查|验证|审计|分析).*(?:漏洞|安全|注入|绕过|权限|接口)",
    r"(?:漏洞|安全|注入|绕过|权限|接口).*(?:测试|检查|验证|审计|分析)",
    r"(?:扫描|探测|枚举|爬取|抓包|逆向|代码审计|渗透测试)",
]
_DIRECTION_COMPILED = [re.compile(p, re.IGNORECASE) for p in _DIRECTION_PATTERNS]

_BARE_PROMPT_STARTERS = [
    r"^(?:redteam\s+(?:on|target)\s+)",
    r"^(?:target\s*[:：]\s*)",
    r"^(?:目标\s*[:：]\s*)",
    r"^(?:对\s+\S+\s+(?:进行|做|执行))",
    r"^(?:测试\s+\S+)",
    r"^(?:看(?:看|一下)\s+\S+)",
    r"^(?:帮我(?:看|跑|测)一下\s+\S+)",
]
_BARE_STARTERS_COMPILED = [re.compile(p, re.IGNORECASE) for p in _BARE_PROMPT_STARTERS]


@dataclass(frozen=True)
class TargetIntent:
    target: str
    target_type: str
    bare_target: bool
    explicit_direction: bool
    all_targets: tuple[str, ...] = ()


def extract_target(prompt: str) -> TargetIntent:
    """Extract target information from a user prompt."""
    text = prompt.strip()
    if not text:
        return TargetIntent(
            target="",
            target_type="unknown",
            bare_target=False,
            explicit_direction=False,
        )

    urls = _URL_RE.findall(text)
    cidrs = _CIDR_RE.findall(text)
    ipv4s = _IPV4_RE.findall(text)
    ipv6s = _IPV6_RE.findall(text)
    domains = _DOMAIN_RE.findall(text)

    url_hosts = set()
    for url in urls:
        host_match = re.search(r"https?://([^/:]+)", url, re.IGNORECASE)
        if host_match:
            url_hosts.add(host_match.group(1).lower())

    filtered_domains = [d for d in domains if d.lower() not in url_hosts]

    primary = ""
    primary_type = "unknown"
    all_targets: list[str] = []

    if urls:
        primary = urls[0]
        primary_type = "url"
        all_targets.extend(urls)
    elif cidrs:
        primary = cidrs[0]
        primary_type = "cidr"
        all_targets.extend(cidrs)
    elif ipv4s:
        primary = ipv4s[0]
        primary_type = "ipv4"
        all_targets.extend(ipv4s)
    elif ipv6s:
        primary = ipv6s[0]
        primary_type = "ipv6"
        all_targets.extend(ipv6s)
    elif filtered_domains:
        primary = filtered_domains[0]
        primary_type = "domain"
        all_targets.extend(filtered_domains)
    elif domains:
        primary = domains[0]
        primary_type = "domain"
        all_targets.extend(domains)

    for group in [urls, cidrs, ipv4s, ipv6s, filtered_domains]:
        for item in group:
            if item not in all_targets:
                all_targets.append(item)

    direction = has_explicit_test_direction(text)
    bare = is_bare_target_prompt(text, primary=primary)

    return TargetIntent(
        target=primary,
        target_type=primary_type,
        bare_target=bare and not direction,
        explicit_direction=direction,
        all_targets=tuple(dict.fromkeys(all_targets)),
    )


def is_bare_target_prompt(prompt: str, *, primary: Optional[str] = None) -> bool:
    """Return True when prompt is only a target plus minimal intake words."""
    text = prompt.strip()
    if not text or not primary:
        return False

    remainder = text.replace(primary, "").strip()
    remainder_clean = re.sub(r"[^\w\u4e00-\u9fff]", "", remainder)
    if len(remainder_clean) <= 12:
        return True

    for pattern in _BARE_STARTERS_COMPILED:
        if pattern.search(text):
            return True

    words = re.findall(r"\S+", text)
    return len(words) <= 4


def has_explicit_test_direction(prompt: str) -> bool:
    """Return True when the user named a concrete test direction."""
    text = prompt.strip()
    if not text:
        return False

    return any(pattern.search(text) for pattern in _DIRECTION_COMPILED)
