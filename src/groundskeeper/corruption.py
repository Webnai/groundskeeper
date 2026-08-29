"""Deliberately injects known-bad examples into a generated dataset.

Real hallucination doesn't happen reliably on cue, and measuring detection
capability against whatever a model happens to hallucinate today would make
"Measured Improvement" unfalsifiable — a lucky run with a well-behaved model
would look like a perfect score for reasons that have nothing to do with the
auditor. Instead, this module takes a set of real, model-generated
`TrainingExample`s and deliberately corrupts a known subset in controlled
ways, producing a **labeled ground-truth set**: which examples are actually
grounded (`label="clean"`) and which aren't (`label="corrupted"`, with the
exact reason recorded). That's what turns "did the agent catch the bad
ones?" into a number instead of a vibe.

Three corruption types, roughly in increasing subtlety:

- `UNRELATED_ANSWER` — swap in the answer to a *different* question
  entirely. The easiest case: the answer has nothing to do with the
  question, let alone the source text.
- `NUMBER_SWAP` — alter a specific number in an otherwise-correct-sounding
  answer (a rate limit, a day count). Plausible-sounding, wrong in one
  detail — the case a naive "does this sound reasonable" check would miss.
- `NEGATION` — flip the polarity of a claim ("is" -> "is not"). Subtle:
  everything else about the sentence is untouched.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from enum import StrEnum

from training_data_bot.models import TrainingExample

_NEGATION_FLIPS: list[tuple[str, str]] = [
    (" is not ", " is "),
    (" is ", " is not "),
    (" are not ", " are "),
    (" are ", " are not "),
    (" does not ", " does "),
    (" does ", " does not "),
    (" may not ", " may "),
    (" may ", " may not "),
    (" must not ", " must "),
    (" must ", " must not "),
    (" cannot ", " can "),
    (" can ", " cannot "),
]

_NUMBER_RE = re.compile(r"\d+(\.\d+)?")


class CorruptionType(StrEnum):
    UNRELATED_ANSWER = "unrelated_answer"
    NUMBER_SWAP = "number_swap"
    NEGATION = "negation"


@dataclass
class LabeledExample:
    """One example plus its ground-truth label for evaluation purposes."""

    example: TrainingExample
    label: str  # "clean" or "corrupted"
    corruption_type: CorruptionType | None
    ground_truth_note: str


def inject_corruption(
    examples: list[TrainingExample],
    corruption_rate: float = 0.4,
    seed: int = 7,
) -> list[LabeledExample]:
    """Corrupt a deterministic (seeded) fraction of examples; label every example."""
    rng = random.Random(seed)
    n_corrupt = max(1, round(len(examples) * corruption_rate)) if examples else 0
    corrupt_indices = set(rng.sample(range(len(examples)), k=min(n_corrupt, len(examples))))

    labeled: list[LabeledExample] = []
    for i, example in enumerate(examples):
        if i not in corrupt_indices:
            labeled.append(LabeledExample(example, "clean", None, "unmodified"))
            continue

        corruption_type, corrupted_output, note = _corrupt_one(example, examples, rng)
        corrupted = example.model_copy(update={"output_text": corrupted_output})
        labeled.append(LabeledExample(corrupted, "corrupted", corruption_type, note))

    return labeled


def _corrupt_one(
    example: TrainingExample, all_examples: list[TrainingExample], rng: random.Random
) -> tuple[CorruptionType, str, str]:
    """Try corruption types in order of preference, falling back if one doesn't apply."""
    if _NUMBER_RE.search(example.output_text):
        swapped = _swap_a_number(example.output_text, rng)
        if swapped != example.output_text:
            return CorruptionType.NUMBER_SWAP, swapped, "Altered a number in the answer"

    for old, new in rng.sample(_NEGATION_FLIPS, k=len(_NEGATION_FLIPS)):
        if old in example.output_text:
            flipped = example.output_text.replace(old, new, 1)
            return CorruptionType.NEGATION, flipped, f"Flipped {old.strip()!r} -> {new.strip()!r}"

    others = [e for e in all_examples if e.id != example.id and e.output_text.strip()]
    swapped_example = rng.choice(others) if others else example
    note = f"Swapped in the answer to a different question: {swapped_example.input_text!r}"
    return CorruptionType.UNRELATED_ANSWER, swapped_example.output_text, note


def _swap_a_number(text: str, rng: random.Random) -> str:
    match = _NUMBER_RE.search(text)
    if not match:
        return text
    original = match.group()
    value = float(original)
    # Multiply by a random factor clearly different from 1.0 (0.4-0.7x or 1.5-2.5x)
    # so the corrupted number is wrong, not just off by rounding.
    factor = rng.choice([rng.uniform(0.4, 0.7), rng.uniform(1.5, 2.5)])
    new_value = value * factor
    new_str = str(round(new_value)) if "." not in original else f"{new_value:.1f}"
    return text[: match.start()] + new_str + text[match.end() :]
