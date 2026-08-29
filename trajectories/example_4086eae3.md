# Trajectory: example `4086eae3`

**Verdict:** ✅ PASS
**Attempts:** 0
**Reason:** Grounded; citation verified against source.

**Question:** What is the initial backoff interval for webhook retries?
**Final answer:** 30 seconds.

## Steps

### 1. `grounding_check`

- Model verdict: **supported**
- Claimed supporting quote: "Webhook delivery is retried up to **5 times** with exponential backoff starting at 30 seconds, doubling each retry, before the webhook is marked as failed and the customer is notified by email."
- Model's reasoning: The passage explicitly states that the exponential backoff starts at 30 seconds, which directly answers the question about the initial backoff interval.

### 2. `span_verify`

- Programmatic check of the claimed quote: verified — quote genuinely found in source
- Fuzzy match ratio: 1.0
