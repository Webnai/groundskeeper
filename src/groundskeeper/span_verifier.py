"""The one non-LLM tool this agent relies on.

The grounding-check LLM call (see `auditor.py`) asks the model to quote its
exact supporting evidence from the source text. This module is what keeps
that honest: it does **not** trust the model's claim that a quote is
"basically what the text says" — it checks, programmatically, whether the
claimed quote actually occurs (verbatim, or close enough to account for
whitespace/punctuation differences) in the source. This is what turns "ask
the model to justify itself" from a vibe into something verifiable.

Exact substring match is tried first (cheap, unambiguous). If that fails, a
sliding-window fuzzy match (stdlib `difflib`, no new dependency) catches
near-verbatim quotes that differ only in whitespace, quote-character style,
or minor punctuation — without being so permissive that a mostly-invented
"close enough" quote would pass.

One thing this module deliberately does NOT trust fuzzy matching for:
**numbers.** A single altered digit in an otherwise-correct, long sentence
("carry over up to 3 unused PTO days" vs. the real "5") is nearly invisible
to edit-distance similarity — a one-character diff in an 85-character
sentence scores ~94% similar, comfortably past a 90% threshold, even though
that one digit *is* the entire factual claim. This was found empirically
while testing this exact module against the number-swap corruption this
project's evaluation deliberately injects (see `corruption.py` and
`CHANGELOG.md`), not designed in from the start. The fix: if the claimed
quote contains any digit sequence, every digit sequence in it must appear
**verbatim** somewhere in the source text, on top of the fuzzy prose match —
fuzzy matching handles prose noise (whitespace, punctuation, quote style),
exact matching handles the numbers that fuzzy matching is structurally
blind to.

A second real false positive, found the same way (a live run, not designed
in from the start): a genuinely correct citation of a Markdown source chunk
scored only ~0.85 similarity and was wrongly escalated, because the source
chunk retained `**bold**` markers around the exact fact being quoted
("**1.5 days per month**") while the model — sensibly — quoted the clean
prose without them. The four extra `*` characters were enough to drag the
ratio under the 0.90 threshold. Since emphasis markers carry no factual
content, `_normalize` strips them from both sides before comparing.

A third, found immediately after fixing the second on the very next real
run: the source said "auto-escalates" (a plain ASCII hyphen, U+002D); the
model's otherwise word-for-word-correct quote said "auto‑escalates" (a
Unicode non-breaking hyphen, U+2011) — visually identical, a different byte.
LLMs routinely substitute typographically "nicer" look-alike punctuation
(smart quotes, en/em dashes, non-breaking hyphens, non-breaking spaces) when
generating text, even when quoting. `_normalize` maps the common look-alikes
to their plain ASCII equivalents before comparing, on both sides, for the
same reason it strips Markdown emphasis: these are presentation artifacts,
not factual content, and treating them as if they were is exactly the kind
of false positive that would erode trust in this tool fast.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

_FUZZY_THRESHOLD = 0.90
_WHITESPACE_RE = re.compile(r"\s+")
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
_MARKDOWN_EMPHASIS_RE = re.compile(r"[*_]{1,2}")
_PUNCTUATION_LOOKALIKES = {
    "‐": "-",  # hyphen
    "‑": "-",  # non-breaking hyphen
    "‒": "-",  # figure dash
    "–": "-",  # en dash
    "—": "-",  # em dash
    "―": "-",  # horizontal bar
    "‘": "'",  # left single quote
    "’": "'",  # right single quote / apostrophe
    "“": '"',  # left double quote
    "”": '"',  # right double quote
    " ": " ",  # non-breaking space
}
_PUNCTUATION_RE = re.compile("|".join(re.escape(k) for k in _PUNCTUATION_LOOKALIKES))


@dataclass
class SpanCheckResult:
    supported: bool
    match_ratio: float
    matched_window: str | None  # best-matching source substring, kept for the trajectory log


def _normalize(text: str) -> str:
    text = _MARKDOWN_EMPHASIS_RE.sub("", text)
    text = _PUNCTUATION_RE.sub(lambda m: _PUNCTUATION_LOOKALIKES[m.group()], text)
    return _WHITESPACE_RE.sub(" ", text).strip().lower()


def verify_span(claimed_quote: str, source_text: str) -> SpanCheckResult:
    """Check whether `claimed_quote` actually occurs in `source_text`."""
    claimed_quote = claimed_quote.strip()
    if not claimed_quote:
        return SpanCheckResult(supported=False, match_ratio=0.0, matched_window=None)

    normalized_quote = _normalize(claimed_quote)
    normalized_source = _normalize(source_text)

    if normalized_quote in normalized_source:
        return SpanCheckResult(supported=True, match_ratio=1.0, matched_window=claimed_quote)

    best_ratio, best_window = _best_fuzzy_window(normalized_quote, normalized_source)
    fuzzy_supported = best_ratio >= _FUZZY_THRESHOLD
    numbers_ok = _numbers_are_verbatim_in_source(normalized_quote, normalized_source)

    return SpanCheckResult(
        supported=fuzzy_supported and numbers_ok,
        match_ratio=round(best_ratio, 4),
        matched_window=best_window,
    )


def _numbers_are_verbatim_in_source(quote: str, source: str) -> bool:
    """Every digit sequence in the quote must appear verbatim in the source.

    Fuzzy prose similarity cannot be trusted for this — see module
    docstring. A quote with no numbers at all trivially passes this check
    (nothing to verify); the fuzzy prose match is doing all the work there.
    """
    source_numbers = _NUMBER_RE.findall(source)
    return all(number in source_numbers for number in _NUMBER_RE.findall(quote))


def _best_fuzzy_window(quote: str, source: str) -> tuple[float, str | None]:
    """Slide a window the length of `quote` across `source`, keep the best-matching one.

    Comparing the quote against the *entire* source with `SequenceMatcher`
    directly would be dominated by the length difference — a 10-word quote
    against a 500-word document scores near zero regardless of content,
    because the ratio counts the whole source as "unmatched." Windowing
    instead compares the quote against same-length slices of the source, so
    the score reflects how close the *best* matching window is, not how
    much of the whole document the quote covers.
    """
    window_size = len(quote)
    if window_size == 0:
        return 0.0, None
    if len(source) <= window_size:
        return SequenceMatcher(None, quote, source).ratio(), (source or None)

    best_ratio = 0.0
    best_window: str | None = None
    step = max(1, window_size // 4)
    for start in range(0, len(source) - window_size + 1, step):
        window = source[start : start + window_size]
        ratio = SequenceMatcher(None, quote, window).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_window = window
    return best_ratio, best_window
