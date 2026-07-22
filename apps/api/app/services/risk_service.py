from enum import StrEnum

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Alert, Run
from app.services.injection_service import InjectionFinding
from app.services.injection_service import Severity as InjectionSeverity
from app.services.pii_service import PIICategory, PIIFinding

# Documented, deterministic point values per finding — the whole scoring
# function is intentionally simple arithmetic (no ML) so a security reviewer
# can look at an Alert and know exactly why the score came out the way it
# did. See docs/TDD.md for the tradeoff against a learned classifier.
PII_WEIGHTS: dict[PIICategory, int] = {
    PIICategory.EMAIL: 5,
    PIICategory.PHONE: 5,
    PIICategory.SSN: 25,
    PIICategory.CREDIT_CARD: 30,
}

INJECTION_WEIGHTS: dict[InjectionSeverity, int] = {
    InjectionSeverity.LOW: 5,
    InjectionSeverity.MEDIUM: 15,
    InjectionSeverity.HIGH: 30,
}

MAX_RISK_SCORE = 100
ALERT_THRESHOLD = 50


class AlertSeverity(StrEnum):
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def compute_risk_score(
    pii_findings: dict[str, list[PIIFinding]],
    injection_findings: dict[str, list[InjectionFinding]],
) -> int:
    score = 0
    for pii_finding_list in pii_findings.values():
        for pii_finding in pii_finding_list:
            score += PII_WEIGHTS.get(pii_finding.category, 0)
    for injection_finding_list in injection_findings.values():
        for injection_finding in injection_finding_list:
            score += INJECTION_WEIGHTS.get(injection_finding.severity, 0)
    return min(score, MAX_RISK_SCORE)


def severity_for_score(score: int) -> AlertSeverity:
    """Only meaningful for scores that have already cleared ALERT_THRESHOLD."""
    if score >= 90:
        return AlertSeverity.CRITICAL
    if score >= 70:
        return AlertSeverity.HIGH
    return AlertSeverity.MEDIUM


async def assess_run(
    db: AsyncSession,
    run: Run,
    pii_findings: dict[str, list[PIIFinding]],
    injection_findings: dict[str, list[InjectionFinding]],
) -> int:
    score = compute_risk_score(pii_findings, injection_findings)
    run.risk_score = score

    # Idempotent: clear any alerts from a previous analysis pass before
    # (maybe) writing fresh ones, so a retried job never duplicates alerts.
    await db.execute(delete(Alert).where(Alert.run_id == run.id))

    if score >= ALERT_THRESHOLD:
        severity = severity_for_score(score)

        if pii_findings:
            categories = sorted(
                {f.category.value for findings in pii_findings.values() for f in findings}
            )
            finding_count = sum(len(f) for f in pii_findings.values())
            db.add(
                Alert(
                    run_id=run.id,
                    category="pii",
                    severity=severity.value,
                    detail=(
                        f"Detected {finding_count} PII finding(s): {', '.join(categories)}"
                    ),
                )
            )

        if injection_findings:
            categories = sorted(
                {f.category.value for findings in injection_findings.values() for f in findings}
            )
            finding_count = sum(len(f) for f in injection_findings.values())
            db.add(
                Alert(
                    run_id=run.id,
                    category="prompt_injection",
                    severity=severity.value,
                    detail=(
                        f"Detected {finding_count} prompt injection finding(s): "
                        f"{', '.join(categories)}"
                    ),
                )
            )

    await db.commit()
    return score
