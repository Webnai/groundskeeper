# Trajectory: example `27f14eee`

**Verdict:** 🔧 FIXED (after retry)
**Attempts:** 1
**Reason:** Grounded after one regeneration attempt.

**Question:** What is Ram's occupation?
**Final answer:** Recruiter

## Steps

### 1. `grounding_check`

- Model verdict: **not_supported**
- Claimed supporting quote: "(none given)"
- Model's reasoning: The source passage states Ram's occupation is "Recruiter", but the candidate answer is "4", which does not match or appear in the passage.

### 2. `retry_generate`

- Agent asked the model to regenerate a grounded answer.
- Revised answer: Recruiter

### 3. `grounding_check`

- Model verdict: **supported**
- Claimed supporting quote: "Occupation: Recruiter"
- Model's reasoning: The passage explicitly states Ram's occupation as Recruiter, directly supporting the answer.

### 4. `span_verify`

- Programmatic check of the claimed quote: verified — quote genuinely found in source
- Fuzzy match ratio: 1.0
