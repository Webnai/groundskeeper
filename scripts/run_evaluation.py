#!/usr/bin/env python
"""Step 3: compare baseline vs agent against the labeled ground truth.

Joins the frozen eval set's ground-truth labels with both the baseline's
and the agent's per-example decisions, computes the primary outcome metric
(grounding-issue catch rate on deliberately corrupted examples) and the
cost side of that tradeoff (false-flag rate on genuinely clean examples),
broken down by corruption type. Writes `output/evaluation_report.md`.

Usage:
    python scripts/run_evaluation.py [--output-dir output/other]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from groundskeeper.report import render_evaluation_markdown
from groundskeeper.serde import load_agent_results, load_baseline_results, load_labeled_dataset

DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "output"


def main(output_dir: Path) -> None:
    labeled = load_labeled_dataset(output_dir / "eval_set.json")
    baseline = load_baseline_results(output_dir / "baseline_results.json")
    agent = load_agent_results(output_dir / "agent_results.json")

    rows = []
    for item in labeled:
        example_id = str(item.example.id)
        baseline_row = baseline[example_id]
        agent_row = agent[example_id]
        rows.append(
            {
                "example_id": example_id,
                "question": item.example.input_text,
                "label": item.label,
                "corruption_type": item.corruption_type.value if item.corruption_type else None,
                "ground_truth_note": item.ground_truth_note,
                "baseline_shipped": baseline_row["shipped"],
                "agent_verdict": agent_row["verdict"],
                "agent_attempts": agent_row["attempts"],
            }
        )

    report_markdown, summary = render_evaluation_markdown(rows)
    (output_dir / "evaluation_report.md").write_text(report_markdown)

    print(report_markdown)
    print(f"\nWrote {output_dir / 'evaluation_report.md'}")
    print(f"\nSummary: {summary}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    main(args.output_dir)
