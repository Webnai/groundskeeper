# Trajectory: example `518b436d`

**Verdict:** ✅ PASS
**Attempts:** 0
**Reason:** Grounded; citation verified against source.

**Question:** How many times is webhook delivery retried before it is considered failed?
**Final answer:** Webhook delivery is retried up to 5 times.

## Steps

### 1. `grounding_check`

- Model verdict: **supported**
- Claimed supporting quote: "Webhook delivery is retried up to **5 times**"
- Model's reasoning: The source passage explicitly states that webhook delivery is retried up to 5 times before being marked as failed, which directly matches the candidate answer.

### 2. `span_verify`

- Programmatic check of the claimed quote: verified — quote genuinely found in source
- Fuzzy match ratio: 1.0
