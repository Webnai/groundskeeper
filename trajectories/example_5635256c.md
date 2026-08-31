# Trajectory: example `5635256c`

**Verdict:** ✅ PASS
**Attempts:** 0
**Reason:** Grounded; citation verified against source.

**Question:** What is the initial backoff interval for webhook retries, and how does it change with each retry?
**Final answer:** The backoff starts at 30 seconds and doubles with each retry.

## Steps

### 1. `grounding_check`

- Model verdict: **supported**
- Claimed supporting quote: "Webhook delivery is retried up to **5 times** with exponential backoff starting at 30 seconds, doubling each retry, before the webhook is marked as failed and the customer is notified by email."
- Model's reasoning: The candidate answer directly reflects the passage's statement that the backoff starts at 30 seconds and doubles with each retry.

### 2. `span_verify`

- Programmatic check of the claimed quote: verified — quote genuinely found in source
- Fuzzy match ratio: 1.0
