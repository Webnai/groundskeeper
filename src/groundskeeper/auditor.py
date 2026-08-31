"""GroundingAuditor: the agent.

For each training example, in order:

1. **Duplicate pre-filter** (cheap, no LLM call) — an exact-duplicate
   (question, answer) pair elsewhere in the batch is escalated immediately.
   Keyed on the pair rather than the answer alone: on short categorical
   answers (survey data — "Yes"/"No"/"24") the same answer text legitimately
   recurs across unrelated questions, which is coincidence, not redundancy.
2. **Grounding check** — an independent LLM call (no memory of however the
   example was originally generated) is asked to judge whether the answer
   is supported by the source passage, and to quote its exact evidence.
   This is the "orchestration" half of the design: the check is a fresh,
   separate opinion, not the same context continuing.
3. **Span verification** — the claimed quote is checked, programmatically
   (`span_verifier.verify_span`), against the actual source text. The
   model's *claim* that it found supporting evidence is never trusted on
   its own; see `span_verifier.py` for a real bug this caught during
   development.
4. **Decision**: PASS (first try) / FIXED (passed after one regeneration
   attempt) / ESCALATED (still fails after the retry budget, or the
   duplicate pre-filter caught it) / DUPLICATE.

Every step is recorded in a `TrajectoryStep` list attached to the
`AuditResult`, so a full, inspectable trajectory is a byproduct of running
this for real, not something reconstructed after the fact.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID

from training_data_bot.ai.base import AIClient
from training_data_bot.core.logging import LogContext, get_logger
from training_data_bot.models import TrainingExample

from .span_verifier import verify_span

_GROUNDING_CHECK_SYSTEM = (
    "You are a strict fact-checker. You produce only valid JSON. "
    "Never include prose or markdown fences."
)

_GROUNDING_CHECK_TEMPLATE = (
    "You will be given a SOURCE PASSAGE and a CANDIDATE ANSWER that claims "
    "to be derived from it. Determine whether the candidate answer is "
    "fully and accurately supported by the source passage — not merely "
    "plausible, but actually stated in the passage.\n\n"
    'Source passage:\n"""\n{source_text}\n"""\n\n'
    "Question the answer responds to: {question}\n"
    'Candidate answer:\n"""\n{answer}\n"""\n\n'
    "If the answer is fully supported, quote the EXACT sentence or phrase "
    "from the source passage (word-for-word, no paraphrasing) that "
    "supports it. If the answer is not supported, contradicts the "
    "passage, or introduces information not present in the passage, say "
    "so and explain what's wrong.\n\n"
    "Respond with ONLY a JSON object, no prose, no markdown fences, in "
    "this exact shape:\n"
    '{{"verdict": "supported" or "not_supported", "supporting_quote": "...", "reason": "..."}}'
)

_REGENERATE_SYSTEM = (
    "You produce only valid JSON. Never include prose or markdown fences."
)

_REGENERATE_TEMPLATE = (
    "A previous answer to this question failed a grounding check.\n\n"
    "Question: {question}\n"
    "Previous answer: {previous_answer}\n"
    "Why it failed: {reason}\n\n"
    "Source passage (this is the ONLY information you may use):\n"
    '"""\n{source_text}\n"""\n\n'
    "Write a corrected answer that is fully and verifiably supported by "
    "the source passage above. If no correct answer is possible from this "
    'passage alone, respond with exactly: "NOT_ANSWERABLE_FROM_SOURCE".\n\n'
    "Respond with ONLY a JSON object, no prose, no markdown fences:\n"
    '{{"answer": "..."}}'
)


class Verdict(StrEnum):
    PASS = "pass"
    FIXED = "fixed"
    ESCALATED = "escalated"
    DUPLICATE = "duplicate"


@dataclass
class TrajectoryStep:
    """One recorded step of the agent's reasoning, in the order it happened."""

    step: str
    detail: dict[str, Any]


@dataclass
class AuditResult:
    example: TrainingExample
    verdict: Verdict
    attempts: int
    trajectory: list[TrajectoryStep] = field(default_factory=list)
    final_reason: str = ""


class GroundingAuditor:
    """Audits a dataset's examples for whether their answers are actually grounded."""

    def __init__(
        self,
        ai_client: AIClient,
        max_retries: int = 1,
        max_concurrency: int = 4,
    ) -> None:
        self.ai_client = ai_client
        self.max_retries = max_retries
        self.max_concurrency = max_concurrency
        self.logger = get_logger("groundskeeper.auditor.GroundingAuditor")

    async def audit_dataset(
        self,
        examples: list[TrainingExample],
        source_lookup: dict[UUID, str],
    ) -> list[AuditResult]:
        """Audit every example. `source_lookup` maps chunk/document id -> source text."""
        duplicate_ids, duplicate_reasons = self._find_duplicates(examples)
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def _audit_with_limit(example: TrainingExample) -> AuditResult:
            if example.id in duplicate_ids:
                return AuditResult(
                    example=example,
                    verdict=Verdict.DUPLICATE,
                    attempts=0,
                    trajectory=[
                        TrajectoryStep("duplicate_prefilter", {"reason": duplicate_reasons[example.id]})
                    ],
                    final_reason=duplicate_reasons[example.id],
                )
            async with semaphore:
                source_text = source_lookup.get(
                    example.source_chunk_id or example.source_document_id, ""
                )
                try:
                    return await self._audit_one(example, source_text)
                except Exception as exc:  # noqa: BLE001 - one persistent failure must not sink the batch
                    self.logger.error("Audit failed for example %s: %s", example.id, exc)
                    return AuditResult(
                        example=example,
                        verdict=Verdict.ESCALATED,
                        attempts=self.max_retries,
                        trajectory=[TrajectoryStep("error", {"exception": str(exc)})],
                        final_reason=f"Auditing itself failed (not a grounding failure): {exc}",
                    )

        return list(await asyncio.gather(*(_audit_with_limit(e) for e in examples)))

    def _find_duplicates(
        self, examples: list[TrainingExample]
    ) -> tuple[set[UUID], dict[UUID, str]]:
        """Exact-duplicate (question, answer) pairs elsewhere in the batch, escalated for free.

        Keyed on the pair, not the answer alone: on short categorical answers
        (survey data — "Yes"/"No"/"24") the same answer text legitimately
        recurs across unrelated questions, which answer-only matching mistook
        for redundancy. A true duplicate is the same question answered the
        same way twice (e.g. via overlapping chunks).
        """
        seen: dict[tuple[str, str], TrainingExample] = {}
        duplicate_ids: set[UUID] = set()
        reasons: dict[UUID, str] = {}
        for example in examples:
            normalized_answer = " ".join(example.output_text.lower().split())
            if not normalized_answer:
                continue
            key = (" ".join(example.input_text.lower().split()), normalized_answer)
            if key in seen:
                duplicate_ids.add(example.id)
                reasons[example.id] = (
                    f"Identical question+answer to example {seen[key].id} "
                    f"(question: {seen[key].input_text!r})"
                )
            else:
                seen[key] = example
        return duplicate_ids, reasons

    async def _audit_one(self, example: TrainingExample, source_text: str) -> AuditResult:
        with LogContext("audit_one", example_id=str(example.id)):
            trajectory: list[TrajectoryStep] = []
            current_answer = example.output_text
            attempts = 0

            while True:
                check = await self._grounding_check(example.input_text, current_answer, source_text)
                trajectory.append(TrajectoryStep("grounding_check", check))

                span_result = None
                if check.get("verdict") == "supported" and check.get("supporting_quote"):
                    span_result = verify_span(check["supporting_quote"], source_text)
                    trajectory.append(
                        TrajectoryStep(
                            "span_verify",
                            {
                                "supported": span_result.supported,
                                "match_ratio": span_result.match_ratio,
                            },
                        )
                    )

                passed = bool(span_result and span_result.supported)
                if passed:
                    verdict = Verdict.PASS if attempts == 0 else Verdict.FIXED
                    reason = (
                        "Grounded; citation verified against source."
                        if attempts == 0
                        else "Grounded after one regeneration attempt."
                    )
                    return AuditResult(
                        example=example.model_copy(update={"output_text": current_answer}),
                        verdict=verdict,
                        attempts=attempts,
                        trajectory=trajectory,
                        final_reason=reason,
                    )

                if attempts >= self.max_retries:
                    reason = self._escalation_reason(check, span_result)
                    self.logger.info("Escalating example %s: %s", example.id, reason)
                    return AuditResult(
                        example=example,
                        verdict=Verdict.ESCALATED,
                        attempts=attempts,
                        trajectory=trajectory,
                        final_reason=reason,
                    )

                attempts += 1
                current_answer = await self._regenerate(
                    example.input_text, current_answer, source_text, check
                )
                trajectory.append(TrajectoryStep("retry_generate", {"revised_answer": current_answer}))

    async def _grounding_check(self, question: str, answer: str, source_text: str) -> dict[str, Any]:
        prompt = _GROUNDING_CHECK_TEMPLATE.format(
            source_text=source_text, question=question, answer=answer
        )
        result = await self.ai_client.generate_json(
            prompt, system=_GROUNDING_CHECK_SYSTEM, temperature=0.0
        )
        if not isinstance(result, dict):
            return {"verdict": "not_supported", "supporting_quote": "", "reason": "Malformed model output"}
        return result

    async def _regenerate(self, question: str, previous_answer: str, source_text: str, check: dict[str, Any]) -> str:
        prompt = _REGENERATE_TEMPLATE.format(
            question=question,
            previous_answer=previous_answer,
            reason=check.get("reason", "not grounded in the source passage"),
            source_text=source_text,
        )
        result = await self.ai_client.generate_json(prompt, system=_REGENERATE_SYSTEM, temperature=0.3)
        if isinstance(result, dict) and result.get("answer"):
            return str(result["answer"])
        return previous_answer  # regeneration itself failed; let the next grounding check fail cleanly

    @staticmethod
    def _escalation_reason(check: dict[str, Any], span_result: Any) -> str:
        if check.get("verdict") == "not_supported":
            return f"Model judged answer not supported: {check.get('reason', 'no reason given')}"
        if span_result is not None and not span_result.supported:
            return (
                f"Model claimed a supporting quote, but it does not verifiably appear "
                f"in the source (best match ratio {span_result.match_ratio})"
            )
        return "Grounding check failed for an unrecognized reason"
