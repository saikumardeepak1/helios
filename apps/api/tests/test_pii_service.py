from datetime import UTC, datetime

from app.models import Span, ToolCall
from app.services.pii_service import PIICategory, scan_span, scan_spans, scan_text


def test_scan_text_finds_no_findings_in_plain_text() -> None:
    assert scan_text("Your order has shipped.", "output") == []


def test_scan_text_detects_email() -> None:
    findings = scan_text("Reach me at jane.doe@example.com for help.", "input")
    assert len(findings) == 1
    assert findings[0].category == PIICategory.EMAIL
    assert findings[0].matched_text == "jane.doe@example.com"


def test_scan_text_detects_ssn() -> None:
    findings = scan_text("SSN on file: 123-45-6789", "input")
    assert any(f.category == PIICategory.SSN for f in findings)


def test_scan_text_detects_phone_number_in_common_formats() -> None:
    for text in ["Call (415) 555-0132", "Call 415-555-0132", "Call +1 415.555.0132"]:
        findings = scan_text(text, "input")
        assert any(f.category == PIICategory.PHONE for f in findings), text


def test_scan_text_detects_a_valid_credit_card_number() -> None:
    # 4111111111111111 is a well-known Visa test number that passes Luhn.
    findings = scan_text("Card on file: 4111111111111111", "input")
    assert any(f.category == PIICategory.CREDIT_CARD for f in findings)


def test_scan_text_does_not_flag_a_luhn_invalid_digit_string() -> None:
    # A 16-digit string that fails the Luhn checksum should not be reported
    # as a credit card — otherwise any long order/tracking number would
    # false-positive as PII.
    findings = scan_text("Tracking number: 1234567890123456", "input")
    assert not any(f.category == PIICategory.CREDIT_CARD for f in findings)


def test_scan_text_does_not_flag_a_short_order_id_as_phone_or_card() -> None:
    findings = scan_text("Order ID: 48213", "input")
    assert findings == []


def _span(**overrides: object) -> Span:
    defaults: dict = {
        "run_id": "00000000-0000-0000-0000-000000000000",
        "kind": "llm_call",
        "started_at": datetime.now(UTC),
        "input": None,
        "output": None,
    }
    defaults.update(overrides)
    span = Span(**defaults)
    span.tool_calls = []
    return span


def test_scan_span_scans_input_and_output() -> None:
    span = _span(
        input={"prompt": "email me at a@example.com"},
        output={"text": "call 415-555-0132"},
    )

    findings = scan_span(span)

    categories = {f.category for f in findings}
    assert PIICategory.EMAIL in categories
    assert PIICategory.PHONE in categories


def test_scan_span_scans_tool_call_arguments_and_results() -> None:
    span = _span()
    span.tool_calls = [
        ToolCall(
            tool_name="lookup_customer",
            arguments={"email": "customer@example.com"},
            result={"ssn": "123-45-6789"},
        )
    ]

    findings = scan_span(span)

    locations = {f.location for f in findings}
    assert "tool_call:lookup_customer:arguments" in locations
    assert "tool_call:lookup_customer:result" in locations


def test_scan_spans_omits_spans_with_no_findings() -> None:
    clean_span = _span(input={"prompt": "hello"})
    clean_span.id = "clean"
    dirty_span = _span(input={"prompt": "a@example.com"})
    dirty_span.id = "dirty"

    results = scan_spans([clean_span, dirty_span])

    assert list(results.keys()) == ["dirty"]
