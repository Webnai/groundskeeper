#!/usr/bin/env python
"""Step 2b: run the Groundskeeper agent against the frozen eval set.

Runs the same examples the baseline saw through the verify -> retry ->
escalate loop (see `groundskeeper.auditor`). Writes `output/agent_results.json`
(machine-readable, used by the evaluation script) and one human-readable
trajectory file per example in `trajectories/` — the required "agent
trajectories" deliverable, produced as a real byproduct of an actual run
rather than written up after the fact.

Usage:
    python scripts/run_agent.py [--max-retries 1] [--max-concurrency 4]
"""

from __future__ import annotations

import argparse
import asyncio
import time
from pathlib import Path

from groundskeeper.ai_backends import get_ai_client
from groundskeeper.auditor import GroundingAuditor
from groundskeeper.report import render_trajectory_markdown
from groundskeeper.serde import load_labeled_dataset, load_source_lookup, save_agent_results

OUTPUT_DIR = Path(__file__).parent.parent / "output"
TRAJECTORIES_DIR = Path(__file__).parent.parent / "trajectories"


async def main(max_retries: int, max_concurrency: int) -> None:
    labeled = load_labeled_dataset(OUTPUT_DIR / "eval_set.json")
    source_lookup = load_source_lookup(OUTPUT_DIR / "source_lookup.json")
    examples = [item.example for item in labeled]

    ai_client = get_ai_client()
    start = time.monotonic()
    try:
        auditor = GroundingAuditor(ai_client, max_retries=max_retries, max_concurrency=max_concurrency)
        results = await auditor.audit_dataset(examples, source_lookup)
    finally:
        await ai_client.close()
    elapsed = time.monotonic() - start

    save_agent_results(results, OUTPUT_DIR / "agent_results.json")

    TRAJECTORIES_DIR.mkdir(exist_ok=True)
    for result in results:
        trajectory_path = TRAJECTORIES_DIR / f"example_{str(result.example.id)[:8]}.md"
        trajectory_path.write_text(render_trajectory_markdown(result))

    by_verdict: dict[str, int] = {}
    for result in results:
        by_verdict[result.verdict.value] = by_verdict.get(result.verdict.value, 0) + 1

    print(f"Agent audited {len(results)} examples in {elapsed:.1f}s")
    for verdict, count in sorted(by_verdict.items()):
        print(f"  {verdict}: {count}")
    print(f"Wrote {OUTPUT_DIR / 'agent_results.json'}")
    print(f"Wrote {len(results)} trajectory file(s) to {TRAJECTORIES_DIR}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--max-concurrency", type=int, default=4)
    args = parser.parse_args()
    asyncio.run(main(args.max_retries, args.max_concurrency))
