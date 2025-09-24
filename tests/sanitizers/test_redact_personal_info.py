import pytest

from ci.sanitizers.redact_personal_info import sanitize_markdown


@pytest.mark.parametrize(
    "raw,expected",
    [
        (
            "Today I paired with Alice (alice@example.com) on feature X.",
            "Today I paired with [REDACTED_NAME] ([REDACTED_EMAIL]) on feature X.",
        ),
        (
            "Call Bob tomorrow about invoices for Charlie.",
            "Call [REDACTED_NAME] tomorrow about invoices for [REDACTED_NAME].",
        ),
    ],
)
def test_sanitize_markdown_removes_personal_info(raw: str, expected: str) -> None:
    sanitized = sanitize_markdown(raw)
    assert sanitized == expected


def test_sanitize_markdown_reports_no_changes_when_clean() -> None:
    clean_text = "Worked on backlog grooming."
    sanitized = sanitize_markdown(clean_text)
    assert sanitized == clean_text
