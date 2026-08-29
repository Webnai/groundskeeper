"""Human-readable rendering of agent trajectories and the evaluation report.

Kept separate from `auditor.py` on purpose: the agent's own code only needs
to *produce* structured trajectory data (a list of `TrajectoryStep`); how
that data gets turned into something a judge can skim in thirty seconds is
a presentation concern, not an agent-behavior concern.
"""

from __future__ import annotations

from .auditor import AuditResult, Verdict

_VERDICT_LABEL = {
    Verdict.PASS: "✅ PASS",
    Verdict.FIXED: "🔧 FIXED (after retry)",
    Verdict.ESCALATED: "🚩 ESCALATED (needs human review)",
    Verdict.DUPLICATE: "🚩 DUPLICATE (needs human review)",
}


def render_trajectory_markdown(result: AuditResult) -> str:
    example = result.example
    lines = [
        f"# Trajectory: example `{str(example.id)[:8]}`",
        "",
        f"**Verdict:** {_VERDICT_LABEL[result.verdict]}",
        f"**Attempts:** {result.attempts}",
        f"**Reason:** {result.final_reason}",
        "",
        f"**Question:** {example.input_text}",
        f"**Final answer:** {example.output_text}",
        "",
        "## Steps",
        "",
    ]

    for i, step in enumerate(result.trajectory, start=1):
        lines.append(f"### {i}. `{step.step}`")
        lines.append("")
        if step.step == "duplicate_prefilter":
            lines.append(f"- No LLM call made. {step.detail['reason']}")
        elif step.step == "grounding_check":
            lines.append(f"- Model verdict: **{step.detail.get('verdict')}**")
            quote = step.detail.get("supporting_quote") or "(none given)"
            lines.append(f"- Claimed supporting quote: \"{quote}\"")
            lines.append(f"- Model's reasoning: {step.detail.get('reason', '(none given)')}")
        elif step.step == "span_verify":
            verdict = "verified — quote genuinely found in source" if step.detail["supported"] else "REJECTED — quote not found in source"
            lines.append(f"- Programmatic check of the claimed quote: {verdict}")
            lines.append(f"- Fuzzy match ratio: {step.detail['match_ratio']}")
        elif step.step == "retry_generate":
            lines.append("- Agent asked the model to regenerate a grounded answer.")
            lines.append(f"- Revised answer: {step.detail['revised_answer']}")
        elif step.step == "error":
            lines.append(f"- Auditing itself failed (not a grounding verdict): {step.detail['exception']}")
        lines.append("")

    return "\n".join(lines)


def render_evaluation_markdown(rows: list[dict]) -> tuple[str, dict]:
    """Build the evaluation report from per-example rows joining ground truth,
    baseline results, and agent results (see scripts/run_evaluation.py)."""
    corrupted = [r for r in rows if r["label"] == "corrupted"]
    clean = [r for r in rows if r["label"] == "clean"]

    def baseline_caught(r: dict) -> bool:
        return not r["baseline_shipped"]

    def agent_caught(r: dict) -> bool:
        return r["agent_verdict"] != "pass"

    baseline_catch_rate = sum(baseline_caught(r) for r in corrupted) / len(corrupted) if corrupted else 0.0
    agent_catch_rate = sum(agent_caught(r) for r in corrupted) / len(corrupted) if corrupted else 0.0
    baseline_false_flag_rate = sum(baseline_caught(r) for r in clean) / len(clean) if clean else 0.0
    agent_false_flag_rate = sum(agent_caught(r) for r in clean) / len(clean) if clean else 0.0

    by_type: dict[str, dict[str, int]] = {}
    for r in corrupted:
        t = r["corruption_type"] or "unknown"
        stats = by_type.setdefault(t, {"total": 0, "agent_caught": 0, "baseline_caught": 0})
        stats["total"] += 1
        stats["agent_caught"] += int(agent_caught(r))
        stats["baseline_caught"] += int(baseline_caught(r))

    lines = [
        "# Evaluation Report",
        "",
        f"{len(rows)} total examples ({len(corrupted)} deliberately corrupted, {len(clean)} clean).",
        "",
        "## Primary outcome: grounding-issue catch rate",
        "",
        "| Metric | Baseline (today) | Groundskeeper Agent | Change |",
        "|---|---|---|---|",
        (
            f"| Catch rate on corrupted examples (n={len(corrupted)}) "
            f"| {baseline_catch_rate:.0%} | {agent_catch_rate:.0%} "
            f"| {agent_catch_rate - baseline_catch_rate:+.0%} |"
        ),
        (
            f"| False-flag rate on clean examples (n={len(clean)}) "
            f"| {baseline_false_flag_rate:.0%} | {agent_false_flag_rate:.0%} "
            f"| {agent_false_flag_rate - baseline_false_flag_rate:+.0%} |"
        ),
        "",
        "## Breakdown by corruption type",
        "",
        "| Type | Cases | Baseline caught | Agent caught |",
        "|---|---|---|---|",
    ]
    for t, stats in sorted(by_type.items()):
        lines.append(f"| {t} | {stats['total']} | {stats['baseline_caught']}/{stats['total']} | {stats['agent_caught']}/{stats['total']} |")

    lines += [
        "",
        "## Per-example detail",
        "",
        "| Question | Label | Type | Baseline | Agent verdict | Attempts |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        q = r["question"][:60] + ("…" if len(r["question"]) > 60 else "")
        lines.append(
            f"| {q} | {r['label']} | {r['corruption_type'] or '-'} "
            f"| {'shipped' if r['baseline_shipped'] else 'flagged'} "
            f"| {r['agent_verdict']} | {r['agent_attempts']} |"
        )

    summary = {
        "baseline_catch_rate": baseline_catch_rate,
        "agent_catch_rate": agent_catch_rate,
        "baseline_false_flag_rate": baseline_false_flag_rate,
        "agent_false_flag_rate": agent_false_flag_rate,
        "n_corrupted": len(corrupted),
        "n_clean": len(clean),
    }
    return "\n".join(lines), summary
