#!/usr/bin/env python
"""Step 2a: run the baseline against the frozen eval set.

The baseline is "the manual process people use today": ship whatever
passes training_data_bot's existing structural checks (empty output, exact
duplicates), with no grounding check at all. No LLM calls — this step is
free and instant.

Usage:
    python scripts/run_baseline.py
"""

from __future__ import annotations

from pathlib import Path

from groundskeeper.baseline import run_baseline
from groundskeeper.serde import load_labeled_dataset, save_baseline_results

OUTPUT_DIR = Path(__file__).parent.parent / "output"


def main() -> None:
    labeled = load_labeled_dataset(OUTPUT_DIR / "eval_set.json")
    examples = [item.example for item in labeled]

    results = run_baseline(examples)
    save_baseline_results(results, OUTPUT_DIR / "baseline_results.json")

    shipped = sum(1 for r in results if r.shipped)
    print(f"Baseline: shipped {shipped}/{len(results)} examples as-is")
    print(f"Wrote {OUTPUT_DIR / 'baseline_results.json'}")


if __name__ == "__main__":
    main()
