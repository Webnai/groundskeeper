# Reproduction Guide

Written for someone starting from a clean environment who has never seen
this repo before.

## Versions this was built and run against

- Python 3.14.7 (anything ≥3.11 should work — no 3.14-specific features used)
- `openai` SDK 3.6.0 (only used for its OpenAI-compatible HTTP client, pointed at Groq)
- `training-data-bot` 0.1.0 (sibling repo, installed editable — see below)

## 1. Get the two repos as siblings

```bash
git clone <this repo's URL> groundskeeper
git clone <training_data_bot repo's URL> data-training-bot
# Both directories must be siblings, e.g.:
#   ~/some-folder/groundskeeper
#   ~/some-folder/data-training-bot
```

`training_data_bot` is not modified by this project and is not published to
PyPI — it's installed as an editable sibling dependency, which is why the
two repos must sit next to each other.

## 2. Install

```bash
cd groundskeeper
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ../data-training-bot
pip install -e ".[dev]"
```

## 3. Get a free API key (no credit card, ever)

```bash
cp .env.example .env
```

Go to [console.groq.com](https://console.groq.com), sign in with email or
Google, create an API key, and add it to `.env`:

```
GROQ_API_KEY=gsk_...
```

That's the only required step — `ai_backends.py` prefers Groq automatically
whenever `GROQ_API_KEY` is set. (If you'd rather use a paid Anthropic/OpenAI
account instead, leave `GROQ_API_KEY` blank and fill in the
`TDB_AI_PROVIDER`/`ANTHROPIC_API_KEY`/`OPENAI_API_KEY` fields instead — the
rest of this guide is identical either way.)

## 4. Run the tests (no API key needed for this step)

```bash
pytest tests/ -q
```

Expected: `16 passed` in well under a second. Every test here runs against
a scripted fake AI client — no network calls, no cost.

## 5. Run the full pipeline (needs the API key from step 3)

```bash
python scripts/generate.py
python scripts/run_baseline.py
python scripts/run_agent.py --max-concurrency 1
python scripts/run_evaluation.py
```

Run these **in this exact order** — each step reads files the previous
step wrote (`output/eval_set.json`, `output/source_lookup.json`,
`output/baseline_results.json`, `output/agent_results.json`), so the
baseline and the agent are guaranteed to run against identical input.

`--max-concurrency 1` on `run_agent.py` matters on Groq's free tier: it has
a per-minute token budget (8,000 TPM at time of writing) that a small
number of concurrent requests on a chatty model can exceed. The agent
handles a transient 429 by retrying with backoff, and a *persistent* one by
escalating that single example rather than crashing the run — but staying
at concurrency 1 avoids hitting the limit at all on a dataset this size.

### Expected output

- `scripts/generate.py`: ~10-15 seconds, prints "Generated 18 examples" (11
  clean, 7 deliberately corrupted).
- `scripts/run_baseline.py`: instant (no LLM calls), prints "shipped 17/18."
- `scripts/run_agent.py`: ~70-90 seconds on Groq's free tier at
  concurrency 1 (mostly rate-limit backoff waits, not compute), prints a
  verdict breakdown (expect something close to: 11 pass, 6 fixed,
  1 duplicate).
- `scripts/run_evaluation.py`: instant, prints and writes
  `output/evaluation_report.md` — expect **100% catch rate on corrupted
  examples, 0% false-flag rate on clean ones**, vs. the baseline's 14%
  catch rate.

**Approximate cost: $0** — every LLM call in this reproduction path goes
through Groq's free tier. **Approximate total real API calls**: 6 for
generation, 29 for the audit (11 examples needed 1 call, 6 needed 3 calls
after a regeneration attempt, 1 cost 0 calls via the duplicate pre-filter).

Exact numbers will vary slightly run to run (LLM output isn't fully
deterministic even at `temperature=0.0`), but the qualitative result — the
agent catches every deliberately corrupted example and the baseline catches
only the one that happens to also be an exact duplicate — should reproduce
reliably.

## 6. Inspect the evidence

- `output/evaluation_report.md` — the full per-example comparison table.
- `trajectories/*.md` — one human-readable trajectory per example; look at
  any file whose verdict is `FIXED` to see the agent catch a corrupted
  answer, ask for a correction, and verify the correction against the
  source before accepting it.
- `CHANGELOG.md` — the real iteration story, including three bugs found
  and fixed during actual runs, with the exact evidence that revealed each
  one.
