import json
import re
from dataclasses import dataclass
from enum import StrEnum

from app.models import Span


class InjectionCategory(StrEnum):
    INSTRUCTION_OVERRIDE = "instruction_override"
    ROLEPLAY_JAILBREAK = "roleplay_jailbreak"
    DELIMITER_ESCAPE = "delimiter_escape"
    PROMPT_EXFILTRATION = "prompt_exfiltration"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class InjectionFinding:
    category: InjectionCategory
    location: str
    matched_text: str
    severity: Severity


# Heuristic, pattern-based detection — explainable and dependency-light for
# v1 (see docs/TDD.md tradeoffs). Each pattern is deliberately narrow to
# keep false positives low; broader coverage is a documented future upgrade.
_PATTERNS: list[tuple[InjectionCategory, Severity, re.Pattern[str]]] = [
    (
        InjectionCategory.INSTRUCTION_OVERRIDE,
        Severity.HIGH,
        re.compile(
            r"\b(ignore|disregard|forget)\s+(all\s+|any\s+)?"
            r"(previous|prior|the\s+above|earlier)\s+(instructions?|prompts?|rules?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        InjectionCategory.INSTRUCTION_OVERRIDE,
        Severity.HIGH,
        re.compile(r"\bnew\s+instructions?\s*:", re.IGNORECASE),
    ),
    (
        InjectionCategory.ROLEPLAY_JAILBREAK,
        Severity.MEDIUM,
        re.compile(
            r"\b(pretend|act)\s+(you\s+are|as\s+if\s+you)\b.{0,40}"
            r"\b(no\s+(restrictions?|rules?|filters?)|unrestricted|without\s+limits?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        InjectionCategory.ROLEPLAY_JAILBREAK,
        Severity.MEDIUM,
        re.compile(r"\byou\s+are\s+now\s+(DAN|in\s+developer\s+mode)\b", re.IGNORECASE),
    ),
    (
        InjectionCategory.DELIMITER_ESCAPE,
        Severity.MEDIUM,
        re.compile(r"<\|(im_start|im_end|endoftext)\|>|\[/?(INST|SYS)\]|<<SYS>>", re.IGNORECASE),
    ),
    (
        InjectionCategory.PROMPT_EXFILTRATION,
        Severity.HIGH,
        re.compile(
            r"\b(repeat|print|reveal|show)\s+(the\s+)?"
            r"(words?\s+above|your\s+(system\s+)?(prompt|instructions))\b",
            re.IGNORECASE,
        ),
    ),
]


def scan_text(text: str, location: str) -> list[InjectionFinding]:
    findings: list[InjectionFinding] = []
    for category, severity, pattern in _PATTERNS:
        for match in pattern.finditer(text):
            findings.append(InjectionFinding(category, location, match.group(), severity))
    return findings


def _stringify(value: dict | None) -> str:
    if value is None:
        return ""
    return json.dumps(value)


def scan_span(span: Span) -> list[InjectionFinding]:
    """Scans only user-supplied input — a model's own output or a tool
    result isn't something an attacker controls, so it isn't in scope here.
    """
    return scan_text(_stringify(span.input), "input")


def scan_spans(spans: list[Span]) -> dict[str, list[InjectionFinding]]:
    """Returns findings keyed by span id, omitting spans with no findings."""
    results: dict[str, list[InjectionFinding]] = {}
    for span in spans:
        findings = scan_span(span)
        if findings:
            results[str(span.id)] = findings
    return results
