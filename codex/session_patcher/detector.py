# -*- coding: utf-8 -*-
"""Refusal detector for Codex CLI session JSONL files."""

from __future__ import annotations

from typing import Dict, List, Optional


class RefusalDetector:
    """Two-tier refusal detection: strong phrases + weak sentence-openers."""

    STRONG_REFUSAL_PHRASES = [
        # Chinese direct refusals
        "我无法协助",
        "我无法帮助",
        "我不能协助",
        "我不能帮助",
        "我不能做",
        "我无法做",
        "我拒绝",
        "我必须拒绝",
        "无法协助你",
        "无法帮助你",
        "我不能为你",
        "我无法为你",
        "这不道德",
        "这是不道德的",
        "这是违法的",
        "这可能违法",
        "超出了我的能力范围",
        "超出我的职责",
        # English direct refusals
        "i cannot assist",
        "i can't assist",
        "i'm unable to assist",
        "i cannot help",
        "i can't help",
        "i'm unable to help",
        "i must decline",
        "i must refuse",
        "against my guidelines",
        "against my policy",
        "violates my",
        "i won't help",
        "i won't assist",
        "as an ai",
        "as a language model",
        "i apologize, but i",
        "i'm sorry, but i can't",
        "not able to provide",
        "not able to assist",
        "cannot provide",
        "cannot comply",
        "this is illegal",
        "this is unethical",
        "would be harmful",
        "potentially harmful",
        # Soft refusal / moralizing
        "建议你通过合法途径",
        "你需要先获得明确授权",
        "出于安全和法律考虑",
        "作为负责的ai",
        "i would recommend considering legal",
        "i suggest you consult",
        "you should seek proper authorization",
        "it would be inappropriate",
        "i'm not comfortable",
        "for ethical reasons",
        "for legal reasons",
        "as a responsible ai",
        "i would advise against",
        "this crosses an ethical boundary",
        "protect user",
        "responsible disclosure",
        "ethical hacking",
        "ethical consideration",
        "code of conduct",
        "terms of service",
        "content policy",
        "usage policy",
    ]

    WEAK_REFUSAL_KEYWORDS = [
        # Chinese, only near start and only when paired with denial context
        "抱歉",
        "很抱歉",
        "对不起",
        "不好意思",
        "恐怕我",
        "我无法",
        "我不能",
        "不允许",
        "禁止",
        # English, only near start and only when paired with denial context
        "sorry",
        "apologize",
        "i cannot",
        "i can't",
        "i'm unable",
        "unable to",
        "not permitted",
        "not allowed",
        "refuse to",
        "i'm afraid i",
        "unfortunately i",
    ]

    NON_REFUSAL_CONTEXT = [
        "确认这个漏洞",
        "确认是否",
        "需要更多证据",
        "need more evidence",
        "not confirmed yet",
        "无法确认",
        "不能确认",
    ]

    def __init__(self, custom_keywords: Optional[Dict[str, List[str]]] = None):
        self.custom_keywords: Dict[str, List[str]] = {}
        if custom_keywords:
            for lang, words in custom_keywords.items():
                self.custom_keywords[lang] = list(words)

    def detect(self, content: str) -> bool:
        if not content:
            return False

        content_lower = content.lower()

        for phrase in self.STRONG_REFUSAL_PHRASES:
            if phrase in content_lower:
                return True

        head = content_lower[:150]
        if not any(marker in content_lower for marker in self.NON_REFUSAL_CONTEXT):
            for keyword in self.WEAK_REFUSAL_KEYWORDS:
                if keyword in head:
                    return True

        for lang_keywords in self.custom_keywords.values():
            for keyword in lang_keywords:
                if keyword.lower() in content_lower:
                    return True

        return False
