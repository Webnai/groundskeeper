"""Tests for span_verifier — the one tool the whole agent's honesty depends on.

If this is wrong, everything downstream is wrong: a broken verifier that's
too permissive would rubber-stamp fabricated citations; one that's too
strict would escalate every genuinely-grounded example as if it weren't.
Both failure directions are tested explicitly below.
"""

from __future__ import annotations

from groundskeeper.span_verifier import verify_span

SOURCE = (
    "Full-time employees accrue paid time off (PTO) at a rate of 1.5 days "
    "per month, for a maximum of 18 days per calendar year. Employees may "
    "carry over up to 5 unused PTO days into the following calendar year."
)


def test_exact_substring_is_supported() -> None:
    result = verify_span("Employees may carry over up to 5 unused PTO days", SOURCE)
    assert result.supported is True
    assert result.match_ratio == 1.0


def test_whitespace_and_case_differences_still_supported() -> None:
    result = verify_span("employees may carry over up to 5 unused pto days", SOURCE)
    assert result.supported is True


def test_fabricated_quote_not_in_source_is_unsupported() -> None:
    result = verify_span("Employees may carry over up to 20 unused PTO days", SOURCE)
    assert result.supported is False


def test_completely_unrelated_quote_is_unsupported() -> None:
    result = verify_span("The API returns an HTTP 429 status code.", SOURCE)
    assert result.supported is False
    assert result.match_ratio < 0.5


def test_empty_quote_is_unsupported() -> None:
    result = verify_span("", SOURCE)
    assert result.supported is False
    assert result.match_ratio == 0.0


def test_quote_longer_than_source_does_not_crash() -> None:
    result = verify_span(SOURCE * 5, "short source")
    assert result.supported is False


def test_minor_punctuation_difference_still_supported() -> None:
    # Curly quotes / minor punctuation shouldn't defeat an otherwise-exact match.
    quoted = "Full-time employees accrue paid time off (PTO) at a rate of 1.5 days per month"
    result = verify_span(quoted, SOURCE)
    assert result.supported is True


def test_a_single_altered_number_is_caught() -> None:
    # The exact failure mode corruption.py's NUMBER_SWAP produces: everything
    # else about the sentence is identical, only the number differs.
    corrupted_claim = "Employees may carry over up to 3 unused PTO days into the following calendar year."
    result = verify_span(corrupted_claim, SOURCE)
    assert result.supported is False


def test_markdown_bold_markers_in_source_do_not_cause_false_negative() -> None:
    # Found on a real run: a chunk retaining **bold** markdown around a fact
    # made an honest, correctly-quoted citation score ~0.85 and get wrongly
    # escalated, because the model (sensibly) quotes clean prose without the
    # `**` markers. See span_verifier.py's module docstring for the full story.
    markdown_source = (
        "Full-time employees accrue paid time off (PTO) at a rate of **1.5 days per\n"
        "month**, for a maximum of **18 days per calendar year**."
    )
    clean_quote = (
        "Full-time employees accrue paid time off (PTO) at a rate of 1.5 days per "
        "month, for a maximum of 18 days per calendar year."
    )
    result = verify_span(clean_quote, markdown_source)
    assert result.supported is True


def test_unicode_hyphen_lookalike_does_not_cause_false_negative() -> None:
    # Found on the very next real run after fixing the markdown-marker case:
    # the source used a plain ASCII hyphen ("auto-escalates"); the model's
    # otherwise word-for-word-correct quote used a Unicode non-breaking
    # hyphen ("auto‑escalates") — visually identical, a different byte.
    source = "the manager has 3 business days before it auto-escalates to the director"
    quote_with_lookalike_hyphen = (
        "the manager has 3 business days before it auto‑escalates to the director"
    )
    result = verify_span(quote_with_lookalike_hyphen, source)
    assert result.supported is True
