# Trajectory: example `428b7224`

**Verdict:** 🔧 FIXED (after retry)
**Attempts:** 1
**Reason:** Grounded after one regeneration attempt.

**Question:** How long does the burst allowance last and what percentage of the per‑minute limit does it represent?
**Final answer:** The burst allowance lasts for a maximum of 10 seconds and equals 20% of the per‑minute limit.

## Steps

### 1. `grounding_check`

- Model verdict: **not_supported**
- Claimed supporting quote: "(none given)"
- Model's reasoning: The source states the burst allowance lasts for a maximum of 10 seconds, not 5 seconds. While the 20% per‑minute limit is correct, the duration is incorrect, so the answer is not fully supported.

### 2. `retry_generate`

- Agent asked the model to regenerate a grounded answer.
- Revised answer: The burst allowance lasts for a maximum of 10 seconds and equals 20% of the per‑minute limit.

### 3. `grounding_check`

- Model verdict: **supported**
- Claimed supporting quote: "All tiers receive a burst allowance equal to 20% of their per-minute limit for a maximum of 10 seconds"
- Model's reasoning: The candidate answer exactly matches the passage's statement about the burst allowance duration and percentage.

### 4. `span_verify`

- Programmatic check of the claimed quote: verified — quote genuinely found in source
- Fuzzy match ratio: 1.0
