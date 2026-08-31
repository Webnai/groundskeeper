# Trajectory: example `eb39a9f4`

**Verdict:** 🔧 FIXED (after retry)
**Attempts:** 1
**Reason:** Grounded after one regeneration attempt.

**Question:** How long can the burst allowance be applied for?
**Final answer:** The burst allowance can be applied for up to 10 seconds.

## Steps

### 1. `grounding_check`

- Model verdict: **not_supported**
- Claimed supporting quote: "All tiers receive a burst allowance equal to **20% of their per-minute limit** for a maximum of 10 seconds, to smooth out short traffic spikes without triggering a 429."
- Model's reasoning: The source states the burst allowance can be applied for a maximum of 10 seconds, whereas the candidate answer claims a maximum of 5 seconds, which contradicts the passage.

### 2. `retry_generate`

- Agent asked the model to regenerate a grounded answer.
- Revised answer: The burst allowance can be applied for up to 10 seconds.

### 3. `grounding_check`

- Model verdict: **supported**
- Claimed supporting quote: "All tiers receive a burst allowance equal to **20% of their per-minute limit** for a maximum of 10 seconds, to smooth out short traffic spikes without triggering a 429."
- Model's reasoning: The passage explicitly states the burst allowance is limited to a maximum of 10 seconds, which directly confirms the answer.

### 4. `span_verify`

- Programmatic check of the claimed quote: verified — quote genuinely found in source
- Fuzzy match ratio: 1.0
