#!/usr/bin/env python
"""Step 2a: run the baseline against the frozen eval set.

The baseline is "the manual process people use today": ship whatever
passes training_data_bot's existing structural checks (empty output, exact
duplicates), with no grounding check at all. No LLM calls — this step is
free and instant.

Usage:
    python scripts/run_baseline.py [--output-dir output/other]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from groundskeeper.baseline import run_baseline
from groundskeeper.serde import load_labeled_dataset, save_baseline_results

DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "output"


def main(output_dir: Path) -> None:
    labeled = load_labeled_dataset(output_dir / "eval_set.json")
    examples = [item.example for item in labeled]

    results = run_baseline(examples)
    save_baseline_results(results, output_dir / "baseline_results.json")

    shipped = sum(1 for r in results if r.shipped)
    print(f"Baseline: shipped {shipped}/{len(results)} examples as-is")
    print(f"Wrote {output_dir / 'baseline_results.json'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    main(args.output_dir)
