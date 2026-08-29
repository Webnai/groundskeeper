# Trajectory: example `707e66cf`

**Verdict:** ✅ PASS
**Attempts:** 0
**Reason:** Grounded; citation verified against source.

**Question:** What HTTP status code does the API return when a client exceeds its per‑minute limit?
**Final answer:** HTTP 429

## Steps

### 1. `grounding_check`

- Model verdict: **supported**
- Claimed supporting quote: "When a client exceeds its per-minute limit, the API returns an **HTTP 429** status code"
- Model's reasoning: The candidate answer exactly matches the status code stated in the source passage.

### 2. `span_verify`

- Programmatic check of the claimed quote: verified — quote genuinely found in source
- Fuzzy match ratio: 1.0
