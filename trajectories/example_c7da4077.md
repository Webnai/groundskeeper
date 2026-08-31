# Trajectory: example `c7da4077`

**Verdict:** ✅ PASS
**Attempts:** 0
**Reason:** Grounded; citation verified against source.

**Question:** What HTTP status code is returned when the daily cap is exceeded on Growth and Enterprise tiers?
**Final answer:** HTTP 402

## Steps

### 1. `grounding_check`

- Model verdict: **supported**
- Claimed supporting quote: "The daily cap, if exceeded, returns an HTTP 402 status code instead, since daily overages are billed rather than blocked on the Growth and Enterprise tiers."
- Model's reasoning: The passage explicitly states that exceeding the daily cap on Growth and Enterprise tiers returns HTTP 402, which matches the candidate answer.

### 2. `span_verify`

- Programmatic check of the claimed quote: verified — quote genuinely found in source
- Fuzzy match ratio: 1.0
