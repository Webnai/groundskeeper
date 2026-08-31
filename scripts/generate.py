#!/usr/bin/env python
"""Step 1: generate the frozen, labeled evaluation dataset.

Loads the synthetic source documents, chunks them, generates QA training
examples with a real LLM call per chunk, then deliberately corrupts a known
subset (see `groundskeeper.corruption`) to produce ground-truth labels.
Writes `output/eval_set.json` and `output/source_lookup.json` — every other
script reads these frozen files rather than regenerating anything, so the
baseline and the agent are guaranteed to run against identical data.

Usage:
    python scripts/generate.py [--corruption-rate 0.4] [--seed 7]
    python scripts/generate.py --source-dir /path/to/other/docs --output-dir output/other
"""

from __future__ import annotations

import argparse
import asyncio
import time
from pathlib import Path

from groundskeeper.pipeline import generate_labeled_dataset
from groundskeeper.serde import save_labeled_dataset, save_source_lookup

DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "output"


async def main(corruption_rate: float, seed: int, source_dir: Path | None, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()

    labeled, source_lookup, documents = await generate_labeled_dataset(
        corruption_rate=corruption_rate, seed=seed, source_dir=source_dir
    )
    elapsed = time.monotonic() - start

    save_labeled_dataset(labeled, output_dir / "eval_set.json")
    save_source_lookup(source_lookup, output_dir / "source_lookup.json")

    n_clean = sum(1 for item in labeled if item.label == "clean")
    n_corrupted = len(labeled) - n_clean
    print(f"Loaded {len(documents)} source document(s)")
    print(f"Generated {len(labeled)} examples in {elapsed:.1f}s")
    print(f"  clean:     {n_clean}")
    print(f"  corrupted: {n_corrupted} (deliberately injected, see ground_truth_note per example)")
    print(f"Wrote {output_dir / 'eval_set.json'}")
    print(f"Wrote {output_dir / 'source_lookup.json'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corruption-rate", type=float, default=0.4)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--source-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    asyncio.run(main(args.corruption_rate, args.seed, args.source_dir, args.output_dir))
