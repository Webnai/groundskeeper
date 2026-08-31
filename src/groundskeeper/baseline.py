"""The baseline: "the manual process people use today."

This is deliberately not a strawman. `training_data_bot`'s own
`QualityEvaluator` already runs exactly these two checks today — empty
output, exact-duplicate detection — and nothing that checks whether an
answer is actually grounded in its source. `QualityEvaluator` only exposes
a dataset-level aggregate report, though, not a per-example decision, so
this module re-applies the same two checks per example to make an
apples-to-apples comparison against the agent's per-example verdicts on the
exact same data possible. No grounding check is performed here — that
absence *is* the baseline.
"""

from __future__ import annotations

from dataclasses import dataclass

from training_data_bot.models import TrainingExample


@dataclass
class BaselineResult:
    example: TrainingExample
    shipped: bool  # would this example ship in the final dataset today?
    reason: str


def run_baseline(examples: list[TrainingExample]) -> list[BaselineResult]:
    # Keyed on (question, answer), not answer alone: on short categorical
    # answers (survey data — "Yes"/"No"/"24") the same answer text legitimately
    # recurs across unrelated questions. Matching on answer-only mistook that
    # coincidence for redundancy; a true duplicate is the same question
    # answered the same way twice (e.g. via overlapping chunks).
    seen: dict[tuple[str, str], TrainingExample] = {}
    results: list[BaselineResult] = []

    for example in examples:
        output = example.output_text.strip()
        if not output:
            results.append(BaselineResult(example, shipped=False, reason="empty output"))
            continue

        key = (" ".join(example.input_text.lower().split()), " ".join(output.lower().split()))
        if key in seen:
            results.append(
                BaselineResult(
                    example, shipped=False, reason=f"exact duplicate of example {seen[key].id}"
                )
            )
            continue

        seen[key] = example
        results.append(
            BaselineResult(example, shipped=True, reason="passed structural checks (no grounding check exists today)")
        )

    return results
