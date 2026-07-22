from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent, Alert, Organization, Run
from app.services.injection_service import InjectionCategory, InjectionFinding
from app.services.injection_service import Severity as InjectionSeverity
from app.services.pii_service import PIICategory, PIIFinding
from app.services.risk_service import (
    ALERT_THRESHOLD,
    AlertSeverity,
    assess_run,
    compute_risk_score,
    severity_for_score,
)


def test_compute_risk_score_is_zero_with_no_findings() -> None:
    assert compute_risk_score({}, {}) == 0


def test_compute_risk_score_sums_pii_finding_weights() -> None:
    findings = {
        "span-1": [
            PIIFinding(PIICategory.EMAIL, "input", "a@example.com", 0.95),
            PIIFinding(PIICategory.SSN, "input", "123-45-6789", 0.9),
        ]
    }
    # email=5, ssn=25
    assert compute_risk_score(findings, {}) == 30


def test_compute_risk_score_sums_injection_finding_weights() -> None:
    findings = {
        "span-1": [
            InjectionFinding(
                InjectionCategory.INSTRUCTION_OVERRIDE,
                "input",
                "ignore previous",
                InjectionSeverity.HIGH,
            ),
            InjectionFinding(
                InjectionCategory.DELIMITER_ESCAPE,
                "input",
                "<|im_start|>",
                InjectionSeverity.MEDIUM,
            ),
        ]
    }
    # high=30, medium=15
    assert compute_risk_score({}, findings) == 45


def test_compute_risk_score_combines_both_detectors() -> None:
    pii = {"span-1": [PIIFinding(PIICategory.CREDIT_CARD, "input", "4111...", 0.9)]}  # 30
    injection = {
        "span-1": [
            InjectionFinding(
                InjectionCategory.PROMPT_EXFILTRATION,
                "input",
                "reveal prompt",
                InjectionSeverity.HIGH,
            )
        ]
    }  # 30
    assert compute_risk_score(pii, injection) == 60


def test_compute_risk_score_caps_at_100() -> None:
    many_findings = {
        f"span-{i}": [PIIFinding(PIICategory.CREDIT_CARD, "input", "x", 0.9)] for i in range(10)
    }
    assert compute_risk_score(many_findings, {}) == 100


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (50, AlertSeverity.MEDIUM),
        (69, AlertSeverity.MEDIUM),
        (70, AlertSeverity.HIGH),
        (89, AlertSeverity.HIGH),
        (90, AlertSeverity.CRITICAL),
        (100, AlertSeverity.CRITICAL),
    ],
)
def test_severity_for_score_boundaries(score: int, expected: AlertSeverity) -> None:
    assert severity_for_score(score) == expected


async def _seed_run(db_session: AsyncSession) -> Run:
    org = Organization(name="Acme Corp")
    agent = Agent(name="support-bot", version="1.0.0")
    org.agents.append(agent)
    db_session.add(org)
    await db_session.flush()

    run = Run(agent_id=agent.id, status="completed", started_at=datetime.now(UTC))
    db_session.add(run)
    await db_session.commit()
    await db_session.refresh(run)
    return run


@pytest.mark.asyncio
async def test_assess_run_below_threshold_sets_score_but_no_alert(
    db_session: AsyncSession,
) -> None:
    run = await _seed_run(db_session)
    pii = {"span-1": [PIIFinding(PIICategory.EMAIL, "input", "a@example.com", 0.95)]}  # 5

    score = await assess_run(db_session, run, pii, {})

    assert score == 5
    assert score < ALERT_THRESHOLD
    assert run.risk_score == 5
    alerts = (await db_session.execute(select(Alert).where(Alert.run_id == run.id))).scalars().all()
    assert alerts == []


@pytest.mark.asyncio
async def test_assess_run_above_threshold_creates_pii_alert(db_session: AsyncSession) -> None:
    run = await _seed_run(db_session)
    pii = {
        "span-1": [
            PIIFinding(PIICategory.CREDIT_CARD, "input", "4111...", 0.9),  # 30
            PIIFinding(PIICategory.SSN, "input", "123-45-6789", 0.9),  # 25
        ]
    }

    score = await assess_run(db_session, run, pii, {})

    assert score == 55
    alerts = (await db_session.execute(select(Alert).where(Alert.run_id == run.id))).scalars().all()
    assert len(alerts) == 1
    assert alerts[0].category == "pii"
    assert alerts[0].severity == "medium"
    assert "credit_card" in alerts[0].detail
    assert "ssn" in alerts[0].detail


@pytest.mark.asyncio
async def test_assess_run_creates_separate_alerts_per_detector(db_session: AsyncSession) -> None:
    run = await _seed_run(db_session)
    pii = {"span-1": [PIIFinding(PIICategory.CREDIT_CARD, "input", "x", 0.9)]}  # 30
    injection = {
        "span-1": [
            InjectionFinding(
                InjectionCategory.INSTRUCTION_OVERRIDE, "input", "x", InjectionSeverity.HIGH
            )
        ]
    }  # 30

    score = await assess_run(db_session, run, pii, injection)

    assert score == 60
    alerts = (await db_session.execute(select(Alert).where(Alert.run_id == run.id))).scalars().all()
    categories = {a.category for a in alerts}
    assert categories == {"pii", "prompt_injection"}


@pytest.mark.asyncio
async def test_assess_run_is_idempotent(db_session: AsyncSession) -> None:
    run = await _seed_run(db_session)
    pii = {"span-1": [PIIFinding(PIICategory.CREDIT_CARD, "input", "x", 0.9)]}
    injection = {
        "span-1": [
            InjectionFinding(
                InjectionCategory.INSTRUCTION_OVERRIDE, "input", "x", InjectionSeverity.HIGH
            )
        ]
    }

    await assess_run(db_session, run, pii, injection)
    await assess_run(db_session, run, pii, injection)

    alerts = (await db_session.execute(select(Alert).where(Alert.run_id == run.id))).scalars().all()
    assert len(alerts) == 2
