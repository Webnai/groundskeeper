"""Tests for GroundingAuditor's decision logic: PASS / FIXED / ESCALATED / DUPLICATE.

Uses a scripted fake AIClient that returns a fixed sequence of canned JSON
responses, one per call — deterministic because each test audits exactly
one (or two, for the duplicate case) examples with `max_concurrency=1`, so
call order is unambiguous. No real API key or network needed.
"""

from __future__ import annotations

from uuid import uuid4

from training_data_bot.ai import FakeAIClient
from training_data_bot.models import TaskType, TrainingExample

from groundskeeper.auditor import GroundingAuditor, Verdict

SOURCE_TEXT = (
    "Full-time employees accrue paid time off (PTO) at a rate of 1.5 days "
    "per month. A corrected answer that is present in the source verbatim "
    "would look exactly like this sentence right here."
)


class ScriptedAIClient(FakeAIClient):
    """Returns canned responses in order, one per call, ignoring prompt content."""

    def __init__(self, responses: list[str]) -> None:
        super().__init__()
        self._responses = list(responses)
        self.call_count = 0

    async def generate(self, prompt: str, **kwargs: object) -> str:
        self.call_count += 1
        self.calls.append(prompt)
        if not self._responses:
            raise AssertionError("ScriptedAIClient ran out of canned responses")
        return self._responses.pop(0)


def _example(output_text: str, question: str = "How many PTO days per month?") -> TrainingExample:
    return TrainingExample(
        input_text=question,
        output_text=output_text,
        task_type=TaskType.QA_GENERATION,
        source_document_id=uuid4(),
    )


async def test_passes_on_first_grounding_check() -> None:
    client = ScriptedAIClient(
        ['{"verdict": "supported", "supporting_quote": "1.5 days per month", "reason": "matches"}']
    )
    example = _example("Employees accrue 1.5 days per month.")
    auditor = GroundingAuditor(client, max_retries=1, max_concurrency=1)

    results = await auditor.audit_dataset([example], {example.source_document_id: SOURCE_TEXT})

    assert len(results) == 1
    assert results[0].verdict == Verdict.PASS
    assert results[0].attempts == 0
    assert client.call_count == 1


async def test_fixed_after_one_successful_retry() -> None:
    client = ScriptedAIClient(
        [
            '{"verdict": "not_supported", "supporting_quote": "", "reason": "wrong number"}',
            '{"answer": "A corrected answer that is present in the source verbatim would look exactly like this sentence right here."}',
            '{"verdict": "supported", "supporting_quote": "A corrected answer that is present in the source verbatim would look exactly like this sentence right here.", "reason": "ok"}',
        ]
    )
    example = _example("Employees accrue 12 days per month.")
    auditor = GroundingAuditor(client, max_retries=1, max_concurrency=1)

    results = await auditor.audit_dataset([example], {example.source_document_id: SOURCE_TEXT})

    assert results[0].verdict == Verdict.FIXED
    assert results[0].attempts == 1
    assert client.call_count == 3


async def test_escalated_when_retry_also_fails() -> None:
    client = ScriptedAIClient(
        [
            '{"verdict": "not_supported", "supporting_quote": "", "reason": "wrong number"}',
            '{"answer": "still wrong"}',
            '{"verdict": "not_supported", "supporting_quote": "", "reason": "still wrong"}',
        ]
    )
    example = _example("Employees accrue 12 days per month.")
    auditor = GroundingAuditor(client, max_retries=1, max_concurrency=1)

    results = await auditor.audit_dataset([example], {example.source_document_id: SOURCE_TEXT})

    assert results[0].verdict == Verdict.ESCALATED
    assert results[0].attempts == 1
    assert "not supported" in results[0].final_reason.lower()


async def test_fabricated_citation_does_not_pass_span_check() -> None:
    """The model claims support with a quote that doesn't actually exist in the source."""
    client = ScriptedAIClient(
        [
            '{"verdict": "supported", "supporting_quote": "a completely made up quote that is not in the source", "reason": "..."}',
            '{"answer": "still not grounded"}',
            '{"verdict": "not_supported", "supporting_quote": "", "reason": "..."}',
        ]
    )
    example = _example("Employees accrue 12 days per month.")
    auditor = GroundingAuditor(client, max_retries=1, max_concurrency=1)

    results = await auditor.audit_dataset([example], {example.source_document_id: SOURCE_TEXT})

    # The model's unverified claim of "supported" must not short-circuit the loop.
    assert results[0].verdict == Verdict.ESCALATED
    span_step = next(s for s in results[0].trajectory if s.step == "span_verify")
    assert span_step.detail["supported"] is False


async def test_duplicate_prefilter_skips_llm_call_for_second_occurrence() -> None:
    """A true duplicate: the same question, answered the same way, twice
    (e.g. via overlapping chunks) — this is genuine redundancy."""
    client = ScriptedAIClient(
        ['{"verdict": "supported", "supporting_quote": "1.5 days per month", "reason": "matches"}']
    )
    first = _example("Employees accrue 1.5 days per month.", question="How many PTO days per month?")
    duplicate = _example("Employees accrue 1.5 days per month.", question="How many PTO days per month?")
    auditor = GroundingAuditor(client, max_retries=1, max_concurrency=1)

    results = await auditor.audit_dataset(
        [first, duplicate],
        {first.source_document_id: SOURCE_TEXT, duplicate.source_document_id: SOURCE_TEXT},
    )

    verdicts = {r.example.id: r.verdict for r in results}
    assert verdicts[first.id] == Verdict.PASS
    assert verdicts[duplicate.id] == Verdict.DUPLICATE
    # Only the first example ever reached the LLM; the duplicate cost zero calls.
    assert client.call_count == 1


async def test_same_answer_different_question_is_not_a_duplicate() -> None:
    """Coincidentally identical short answers to different questions (common
    on categorical/survey data — "Yes"/"No"/"24") must NOT be treated as
    redundant: they're two different facts that happen to render the same."""
    client = ScriptedAIClient(
        [
            '{"verdict": "supported", "supporting_quote": "1.5 days per month", "reason": "matches"}',
            '{"verdict": "supported", "supporting_quote": "1.5 days per month", "reason": "matches"}',
        ]
    )
    first = _example("1.5 days per month.", question="How many PTO days does Alice get per month?")
    same_answer_different_fact = _example(
        "1.5 days per month.", question="How many PTO days does Bob get per month?"
    )
    auditor = GroundingAuditor(client, max_retries=1, max_concurrency=1)

    results = await auditor.audit_dataset(
        [first, same_answer_different_fact],
        {
            first.source_document_id: SOURCE_TEXT,
            same_answer_different_fact.source_document_id: SOURCE_TEXT,
        },
    )

    verdicts = {r.example.id: r.verdict for r in results}
    assert verdicts[first.id] == Verdict.PASS
    assert verdicts[same_answer_different_fact.id] == Verdict.PASS
    # Both distinct questions actually reached the grounding check.
    assert client.call_count == 2


async def test_persistent_ai_failure_on_one_example_does_not_crash_the_batch() -> None:
    """Found via a real run against Groq's free tier: a persistent rate-limit
    error on one example must not take down the whole batch, the same way
    TaskManager/BaseLoader elsewhere in this stack degrade gracefully."""

    class AlwaysFailsClient(ScriptedAIClient):
        async def generate(self, prompt: str, **kwargs: object) -> str:
            self.call_count += 1
            raise RuntimeError("simulated persistent rate limit")

    good_client = ScriptedAIClient(
        ['{"verdict": "supported", "supporting_quote": "1.5 days per month", "reason": "matches"}']
    )
    broken = _example("broken", question="Q-broken?")
    fine = _example("Employees accrue 1.5 days per month.", question="Q-fine?")

    class MixedClient(ScriptedAIClient):
        def __init__(self) -> None:
            super().__init__([])

        async def generate(self, prompt: str, **kwargs: object) -> str:
            self.call_count += 1
            if "Q-broken?" in prompt:
                raise RuntimeError("simulated persistent rate limit")
            return await good_client.generate(prompt, **kwargs)

    auditor = GroundingAuditor(MixedClient(), max_retries=1, max_concurrency=2)
    results = await auditor.audit_dataset(
        [broken, fine],
        {broken.source_document_id: SOURCE_TEXT, fine.source_document_id: SOURCE_TEXT},
    )

    verdicts = {r.example.id: r.verdict for r in results}
    assert verdicts[broken.id] == Verdict.ESCALATED
    assert "not a grounding failure" in next(r for r in results if r.example.id == broken.id).final_reason
    assert verdicts[fine.id] == Verdict.PASS
