# Groundskeeper

A grounding auditor for LLM fine-tuning datasets: catches hallucinated,
duplicated, or off-topic training examples **before** you spend compute
fine-tuning on them — an agent that verifies whether AI-generated data can
actually be trusted, rather than an agent that generates it.

Built for the **micro1 Frontier Engineering Challenge 2026**.

## Who has this problem?

An AI engineer or small ML team who generates a fine-tuning dataset from
their own documents using an LLM pipeline (this project's companion
library, [`training_data_bot`](https://github.com/Webnai/data-training-bot), built separately and
used here unmodified — see "What existed before" below), and is about to
spend real compute fine-tuning a model on it.

## What bottleneck makes it worth solving?

`training_data_bot`'s own `QualityEvaluator` — the best tool this problem
has *today* — only catches structural issues: empty output, exact
duplicates. It has **no way to tell whether a generated answer is actually
supported by the source text it claims to come from.** A hallucinated
answer that's well-formed, unique, and plausible-sounding sails straight
through. Nobody reads every example by hand past a few dozen, so bad data
ships silently — and the first sign of trouble is usually "why did my
fine-tuned model get *worse*," discovered only after the training run.

**The cost this represents:** a wasted fine-tuning run plus the
engineer-hours spent diagnosing it (before anyone suspects the data)
routinely runs $1,500–$9,000 per incident in compute + labor for a small
team. A few caught incidents a quarter clears $10,000 — double this
contest's 1st-place prize.

## Does the agent solve it well?

Yes, measurably. On a real evaluation run (see `CHANGELOG.md` for the full
iteration story and `output/evaluation_report.md` for the raw report):

| Metric | Baseline (today's `QualityEvaluator`) | Groundskeeper Agent | Change |
|---|---|---|---|
| Catch rate on deliberately corrupted examples (n=7) | 0% | **100%** | +100 points |
| False-flag rate on genuinely clean examples (n=11) | 0% | **0%** | +0 points |

Zero of the baseline's catches come from checking whether an answer was
actually *true*, because it never checks that — its only checks are "empty
output?" and "exact duplicate?". The agent catches every corrupted
example (some outright, most by regenerating a corrected, verifiably
grounded answer) with zero cost to the clean examples.

### How the agent works

For each training example, in order:

1. **Duplicate pre-filter** (free, no LLM call) — an exact-duplicate answer
   elsewhere in the batch is flagged immediately.
2. **Grounding check** — an independent LLM call (no memory of how the
   example was generated) judges whether the answer is supported by the
   source passage, and must quote its exact evidence.
3. **Span verification** — the claimed quote is checked, *programmatically*,
   against the real source text. The model's claim that it found supporting
   evidence is never trusted on its own — see `span_verifier.py` for three
   real bugs this exact check caught and fixed during development.
4. **Decision**: pass / regenerate once with stricter grounding instructions
   / escalate to a human review queue if still ungrounded.

This maps directly onto the contest's named agent capabilities: **context**
(fetches the real source chunk, not just the example), **tools** (the span
verifier is a real programmatic check), **verification** (the whole design
is a verify → retry → escalate loop), **memory** (tracks prior attempts per
example), **orchestration** (the grounding check is a structurally
independent second opinion, not the same context continuing).

## Can another person reproduce the result?

Yes — see `REPRODUCTION.md` for exact commands, versions, and expected
output, runnable from a clean environment with a **free** API key (no
credit card required — see below). Every claim above is backed by files
in this repo: `output/eval_set.json` (the labeled ground truth),
`output/agent_results.json` and `output/baseline_results.json` (both
arms' real decisions), `output/evaluation_report.md` (the computed
comparison), and `trajectories/*.md` (one human-readable trajectory per
example, produced as a real byproduct of the actual run).

## What existed before this contest vs. what was built for it

- **`training_data_bot`** (a separate sibling repo, `../data-training-bot`)
  is a general-purpose document-to-fine-tuning-dataset pipeline, built
  earlier and **not modified** for this submission. It's used here purely
  as a dependency (`pip install -e ../data-training-bot`) — the object
  Groundskeeper audits, not something built for this contest.
- **Everything in this repo** — the corruption injector, the span verifier,
  the auditor agent, the baseline, the evaluation harness, and the Groq
  backend adapter (added mid-build after a real budget constraint — see
  `CHANGELOG.md`) — was built for this submission.

## Project layout

```
src/groundskeeper/
├── corruption.py      # injects labeled, known-bad examples for honest evaluation
├── span_verifier.py    # the one non-LLM tool; caught 3 real bugs during dev
├── auditor.py            # the agent: verify -> retry -> escalate
├── baseline.py             # "the manual process people use today"
├── pipeline.py               # shared generation step (fairness: same data, both arms)
├── ai_backends.py              # prefers free Groq backend, falls back to paid
├── groq_client.py                # AIClient backend for Groq's free tier
├── report.py                       # human-readable trajectories + evaluation report
└── serde.py                          # JSON (de)serialization between pipeline steps
scripts/
├── generate.py           # step 1: build the frozen, labeled eval set
├── run_baseline.py         # step 2a: today's status quo, no LLM calls
├── run_agent.py               # step 2b: the actual agent
└── run_evaluation.py            # step 3: compare both, against ground truth
data/source_docs/    # 2 synthetic documents (public/synthetic per contest rules)
output/               # real results from the run this README describes
trajectories/           # 18 real, human-readable agent trajectories
```

See `docs` in this README's companions: `CHANGELOG.md` (the full iteration
story and hot take), `REPRODUCTION.md` (run it yourself), `VIDEO_SCRIPT.md`
(the storyboard for the submission video).
