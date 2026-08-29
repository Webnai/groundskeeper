# Video Script (target: under 5 minutes)

A storyboard to record from directly — read the talking points, run the
commands shown, show the files indicated. Actual numbers below are the real
results from this repo's `output/` — if you rerun before recording, use
whatever your fresh run actually produces instead of these exact figures.

---

## 0:00–0:40 — The problem

**Say:** "If you generate a fine-tuning dataset with an LLM pipeline — questions
and answers pulled from your own documents — the failure mode that actually
costs you money isn't a crash. It's an answer that's well-formed, unique,
and completely made up, sitting in your dataset next to a hundred correct
ones. Nobody reads all of them by hand, so it ships, you fine-tune on it,
and the model gets *worse* for reasons nobody can see until much later.
That's the bottleneck this project solves."

**Show:** `README.md`, scrolled to the "Who has this problem" section.

## 0:40–1:15 — The baseline

**Say:** "The tool this data usually goes through already has quality checks —
empty answers, exact duplicates. It has no way to tell if an answer is
actually *true*. That's the baseline: today's status quo, unchanged."

**Run:**
```bash
python scripts/run_baseline.py
```
**Show:** the printed line: `Baseline: shipped 17/18 examples as-is`.

**Say:** "Seventeen out of eighteen. One of our seven deliberately corrupted
examples got caught — not because anything checked if it was true, but
because it happened to be an exact copy of another answer."

## 1:15–2:45 — One real execution, start to finish

**Run:**
```bash
python scripts/run_agent.py --max-concurrency 1
```

**Say (while it runs):** "This is the actual agent. For every example: an
independent model call checks whether the answer is really supported by the
source passage and has to quote its evidence. Then — this part matters — a
plain Python function checks whether that quoted evidence *actually appears*
in the source. The model's claim is never taken on faith. If it fails, the
agent asks for a corrected answer once, checks again, and only gives up to a
human reviewer if it still can't ground it."

**Show:** open `trajectories/example_3cab9a9a.md` (a real FIXED case from
this repo's run: the question asks the Growth tier's per-minute limit, the
generated answer said 257, the grounding check catches it, the agent
regenerates 600, and the span verifier confirms it against the source
verbatim). If you reran the pipeline yourself, pick any file in
`trajectories/` whose verdict is FIXED instead. Read the four steps out
loud: original wrong number → grounding check catches it → regenerated
answer → verified against source.

**Say:** "That's a training example that was factually wrong, caught,
corrected, and re-verified — automatically, in one pass."

## 2:45–3:30 — The comparison

**Run:**
```bash
python scripts/run_evaluation.py
```

**Show:** the printed table — catch rate on corrupted examples, false-flag
rate on clean ones.

**Say:** "Baseline: 14% catch rate. The agent: 100% — every deliberately
corrupted example, caught or fixed — with zero false flags on the eleven
genuinely clean examples. Same data, same task, only difference is whether
grounding gets checked at all."

## 3:30–4:30 — The changelog: what actually happened

**Show:** `CHANGELOG.md`.

**Say:** "This wasn't the first version. The single most important fix: pure
string-similarity matching is structurally blind to a single wrong number in
a long, otherwise-correct sentence — a one-character diff in an 85-character
sentence scores over 90% similar. I found that from a failing test before
the first real run, and it's why numbers get an exact-match check on top of
the fuzzy prose check — without that fix, the agent would have silently
passed the majority of our corrupted examples, since most of them are wrong
numbers.

Two more bugs showed up only against real model output: Markdown bold
markers around a fact, and a Unicode hyphen the model substituted while
quoting — both made a genuinely correct citation score just under threshold
and get wrongly escalated. Both fixed the same way: normalize formatting
noise out before comparing, don't compare it."

**Say (the "removed" experiment):** "The experiment I effectively removed was
trusting fuzzy similarity as sufficient on its own — it's still there, but
only as one layer of three now, not the whole check."

## 4:30–5:00 — Hot take and close

**Say:** "The lesson that generalizes: when you verify AI output against a
source of truth, don't reach for one similarity score and a threshold.
Decompose it — numbers need exact matching, formatting needs normalization,
and only what's left should go through fuzzy matching. All three bugs here
were invisible in hand-written unit tests and only showed up against real
model output. No amount of synthetic testing replaces at least one real run
before you trust your numbers.

Full reproduction guide, raw evidence, and all eighteen trajectories are in
the repo."

**Show:** `REPRODUCTION.md` for two seconds, end on the repo file tree.
