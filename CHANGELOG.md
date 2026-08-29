# Improvement Changelog

Every stage below is a real event from actually building and running this
project — including the ones that failed, and the exact evidence that drove
the next decision. Full raw evidence lives in `output/*.json`,
`output/evaluation_report.md`, and `trajectories/*.md`.

| Stage | What was tried and why | Evidence | Decision / learning |
|---|---|---|---|
| **Baseline** | Ran `training_data_bot`'s existing `QualityEvaluator` heuristics (empty-output, exact-duplicate) per example — "the manual process people use today," no grounding check exists. | Shipped 17/18 examples as-is on the real eval set; the one catch was an accidental duplicate, not a grounding catch. | Established the starting point: **0% of catches are grounding-aware.** |
| **Iteration 1** | Built the agent's core loop: grounding-check LLM call + fuzzy string-similarity span verification (threshold 0.90) + retry + escalate. | Unit tests (scripted fake AI client) passed — but a targeted test against the exact corruption type this project injects (`NUMBER_SWAP`) failed: a single-digit change in an 85-character sentence scored 93.9% similarity, comfortably over the threshold. | **Removed pure fuzzy matching as sufficient on its own.** Numbers are structurally invisible to edit-distance similarity — a wrong digit in an otherwise-correct sentence barely moves the score. Added a hard rule: any digit sequence in a claimed quote must appear *verbatim* in the source, independent of the fuzzy prose score. |
| **Provider pivot** | Attempted the real evaluation run against Anthropic, then OpenAI. Both accounts turned out to be unfunded (a workspace-auth issue, then zero credit on two separate keys) — a real resource constraint, not a hypothetical one. | `AIClientError`/`RateLimitError` from both providers, confirmed via live API responses. | Added `GroqClient` (Groq's genuinely free, no-card developer tier, OpenAI-compatible endpoint) as a **new file in this repo**, implementing the same `AIClient` interface `training_data_bot` defines — zero changes to the underlying library. This is the provider-agnostic design paying off against a real constraint, not a design goal stated in the abstract. |
| **Iteration 2** | First real run against real data (18 examples, Groq `openai/gpt-oss-120b`, `max_concurrency=4`). | Run crashed entirely: a persistent rate-limit error on one example propagated through `asyncio.gather` and killed the whole batch — `training_data_bot`'s own `TaskManager`/`BaseLoader` isolate per-item failures; this agent's loop hadn't, yet. | Added the same "one bad item doesn't sink the batch" isolation used elsewhere in this stack: a persistent per-example failure now becomes an `ESCALATED` verdict with the error recorded, not a crash. Also dropped concurrency to 1 to respect the free tier's token-per-minute budget. |
| **Iteration 3** | Reran with the resilience fix. Completed successfully — but one genuinely **clean** example was wrongly escalated. | Trajectory showed the model's claimed quote ("...accrue paid time off (PTO) at a rate of 1.5 days per month...") scored only ~0.85 against the source. Root cause, found by pulling the exact source chunk: it retained Markdown `**bold**` markers around the fact (`**1.5 days per month**`); the model — correctly — quoted clean prose without them. Four stray `*` characters dragged the score under threshold. | Fixed `span_verifier._normalize` to strip Markdown emphasis markers on both sides before comparing — they carry no factual content. |
| **Iteration 4** | Reran immediately after the Markdown fix. | A **different** clean example was wrongly escalated: the source said "auto-escalates" (plain ASCII hyphen); the model's otherwise word-for-word-correct quote said "auto‑escalates" (Unicode non-breaking hyphen, U+2011) — visually identical, a different byte. | Added a small lookalike-punctuation table (hyphens/dashes, smart quotes, non-breaking space) to `_normalize`. LLMs routinely substitute typographically "nicer" punctuation even when quoting verbatim; treating that as a grounding failure would erode trust in the tool for the wrong reason. |
| **Final** | Reran with all fixes combined. | **100% catch rate on 7 deliberately corrupted examples, 0% false-flag rate on 11 genuinely clean examples** (baseline: 14% catch rate). See `output/evaluation_report.md` for the full per-example table. | The main contribution isn't the grounding-check prompt — it's the span-verification layer, which went through three real, evidence-driven corrections before it stopped producing false positives on completely legitimate citations. |

## Main failure mode and hot take

**The failure mode that showed up three separate times, in three different
shapes, was the same underlying mistake: trusting string similarity to mean
semantic correctness without checking *what kind* of difference caused the
score to drop.** A missing digit, a Markdown asterisk, and a Unicode hyphen
all produce the same symptom — "similarity score dipped below threshold" —
for three completely different reasons, only one of which (the missing
digit) is an actual grounding failure. The other two are formatting noise
that happens to look identical to content drift if you only look at a
single scalar similarity number.

**The practical lesson for building more reliable agents:** when a
verification step relies on comparing AI-generated text against a source of
truth, don't reach for one generic similarity metric and a threshold and
call it done. Decompose the comparison by *what kind of content* you're
checking — numbers need exact matching (edit distance is structurally blind
to a single wrong digit in a long sentence); prose formatting needs
normalization, not comparison (Markdown markers, typographic punctuation
substitutions, and whitespace are presentation, not content); only what's
left after removing both categories should go through fuzzy matching. Every
one of these three bugs was invisible in unit tests with hand-written
inputs and only surfaced against real model output — which is itself the
broader lesson: a verification tool's hardest bugs come from the exact
inputs it exists to handle (real LLM output), and no amount of synthetic
testing substitutes for at least one real run before you trust the numbers.
