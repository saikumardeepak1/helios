import json
import re
from dataclasses import dataclass
from enum import StrEnum

from app.models import Span


class PIICategory(StrEnum):
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"


@dataclass(frozen=True)
class PIIFinding:
    category: PIICategory
    location: str
    matched_text: str
    confidence: float


_EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_PHONE_PATTERN = re.compile(
    r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b"
)
_CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,16}\b")


def _luhn_checksum(digits: str) -> bool:
    total = 0
    reverse_digits = digits[::-1]
    for i, char in enumerate(reverse_digits):
        n = int(char)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def scan_text(text: str, location: str) -> list[PIIFinding]:
    findings: list[PIIFinding] = []

    for match in _EMAIL_PATTERN.finditer(text):
        findings.append(PIIFinding(PIICategory.EMAIL, location, match.group(), confidence=0.95))

    for match in _SSN_PATTERN.finditer(text):
        findings.append(PIIFinding(PIICategory.SSN, location, match.group(), confidence=0.9))

    for match in _PHONE_PATTERN.finditer(text):
        findings.append(PIIFinding(PIICategory.PHONE, location, match.group(), confidence=0.7))

    for match in _CREDIT_CARD_PATTERN.finditer(text):
        digits = re.sub(r"[ -]", "", match.group())
        if len(digits) in (13, 14, 15, 16) and _luhn_checksum(digits):
            findings.append(
                PIIFinding(PIICategory.CREDIT_CARD, location, match.group(), confidence=0.9)
            )

    return findings


def _stringify(value: dict | None) -> str:
    if value is None:
        return ""
    return json.dumps(value)


def scan_span(span: Span) -> list[PIIFinding]:
    findings: list[PIIFinding] = []
    findings.extend(scan_text(_stringify(span.input), "input"))
    findings.extend(scan_text(_stringify(span.output), "output"))

    for tool_call in span.tool_calls:
        findings.extend(
            scan_text(_stringify(tool_call.arguments), f"tool_call:{tool_call.tool_name}:arguments")
        )
        findings.extend(
            scan_text(_stringify(tool_call.result), f"tool_call:{tool_call.tool_name}:result")
        )

    return findings


def scan_spans(spans: list[Span]) -> dict[str, list[PIIFinding]]:
    """Returns findings keyed by span id, omitting spans with no findings."""
    results: dict[str, list[PIIFinding]] = {}
    for span in spans:
        findings = scan_span(span)
        if findings:
            results[str(span.id)] = findings
    return results
