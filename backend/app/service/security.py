from __future__ import annotations

import re
from typing import List

INJECTION_PATTERNS: List[re.Pattern] = [
    re.compile(r"(?i)(ignore|disregard|forget).*(previous|above|prior).*(instruction|prompt|rule)"),
    re.compile(r"(?i)system\s*prompt"),
    re.compile(r"(?i)you\s+are\s+now"),
    re.compile(r"(?i)act\s+as\s+"),
    re.compile(r"(?i)new\s+instruction"),
    re.compile(r"(?i)(reveal|show|tell|display).*(prompt|instruction|rule|system)"),
    re.compile(r"이전\s*(지시|명령|규칙).*(무시|잊어)"),
    re.compile(r"시스템\s*프롬프트"),
    re.compile(r"너는?\s*이제"),
    re.compile(r"(?i)jailbreak"),
    re.compile(r"(?i)DAN\s*mode"),
]

FORBIDDEN_OUTPUT_PATTERNS: List[re.Pattern] = [
    re.compile(r"(?i)api[_\s]*key"),
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    re.compile(r"(?i)(SELECT|INSERT|UPDATE|DELETE)\s+.*(FROM|INTO|SET|WHERE)", re.DOTALL),
]


def detect_injection(message: str) -> bool:
    for pattern in INJECTION_PATTERNS:
        if pattern.search(message):
            return True
    return False


def validate_output(response: str) -> bool:
    for pattern in FORBIDDEN_OUTPUT_PATTERNS:
        if pattern.search(response):
            return False
    return True


def validate_output_length(response: str, max_length: int) -> bool:
    return len(response) <= max_length
