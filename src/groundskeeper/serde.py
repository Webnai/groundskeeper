"""JSON (de)serialization for the eval set, source lookup, and results.

Every script (`generate.py`, `run_baseline.py`, `run_agent.py`,
`run_evaluation.py`) works from the exact same frozen files on disk instead
of regenerating anything — this is what guarantees the baseline and the
agent are compared against identical data, and it's what makes the whole
run reproducible from saved state instead of needing a fresh (costly,
non-deterministic) generation pass every time.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from training_data_bot.models import TrainingExample

from .auditor import AuditResult
from .baseline import BaselineResult
from .corruption import CorruptionType, LabeledExample


def save_labeled_dataset(labeled: list[LabeledExample], path: Path) -> None:
    payload = [
        {
            "example": item.example.model_dump(mode="json"),
            "label": item.label,
            "corruption_type": item.corruption_type.value if item.corruption_type else None,
            "ground_truth_note": item.ground_truth_note,
        }
        for item in labeled
    ]
    path.write_text(json.dumps(payload, indent=2))


def load_labeled_dataset(path: Path) -> list[LabeledExample]:
    payload = json.loads(path.read_text())
    return [
        LabeledExample(
            example=TrainingExample.model_validate(row["example"]),
            label=row["label"],
            corruption_type=CorruptionType(row["corruption_type"]) if row["corruption_type"] else None,
            ground_truth_note=row["ground_truth_note"],
        )
        for row in payload
    ]


def save_source_lookup(source_lookup: dict[UUID, str], path: Path) -> None:
    path.write_text(json.dumps({str(k): v for k, v in source_lookup.items()}, indent=2))


def load_source_lookup(path: Path) -> dict[UUID, str]:
    raw = json.loads(path.read_text())
    return {UUID(k): v for k, v in raw.items()}


def save_baseline_results(results: list[BaselineResult], path: Path) -> None:
    payload = [
        {"example_id": str(r.example.id), "shipped": r.shipped, "reason": r.reason} for r in results
    ]
    path.write_text(json.dumps(payload, indent=2))


def load_baseline_results(path: Path) -> dict[str, dict]:
    payload = json.loads(path.read_text())
    return {row["example_id"]: row for row in payload}


def save_agent_results(results: list[AuditResult], path: Path) -> None:
    payload = [
        {
            "example_id": str(r.example.id),
            "verdict": r.verdict.value,
            "attempts": r.attempts,
            "final_reason": r.final_reason,
            "final_answer": r.example.output_text,
            "trajectory": [{"step": s.step, "detail": s.detail} for s in r.trajectory],
        }
        for r in results
    ]
    path.write_text(json.dumps(payload, indent=2))


def load_agent_results(path: Path) -> dict[str, dict]:
    payload = json.loads(path.read_text())
    return {row["example_id"]: row for row in payload}
