# Trajectory: example `248caf41`

**Verdict:** 🔧 FIXED (after retry)
**Attempts:** 1
**Reason:** Grounded after one regeneration attempt.

**Question:** What is the maximum number of PTO days a full-time employee can accrue in a calendar year?
**Final answer:** 18 days per calendar year

## Steps

### 1. `grounding_check`

- Model verdict: **not_supported**
- Claimed supporting quote: "for a maximum of 18 days per calendar year"
- Model's reasoning: The source states the maximum is 18 days per calendar year, but the candidate answer claims 10 days, which contradicts the passage.

### 2. `retry_generate`

- Agent asked the model to regenerate a grounded answer.
- Revised answer: 18 days per calendar year

### 3. `grounding_check`

- Model verdict: **supported**
- Claimed supporting quote: "for a maximum of 18 days per calendar year"
- Model's reasoning: The candidate answer exactly matches the statement in the source that full-time employees have a maximum of 18 PTO days per calendar year.

### 4. `span_verify`

- Programmatic check of the claimed quote: verified — quote genuinely found in source
- Fuzzy match ratio: 1.0
