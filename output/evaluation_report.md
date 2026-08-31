# Evaluation Report

18 total examples (7 deliberately corrupted, 11 clean).

## Primary outcome: grounding-issue catch rate

| Metric | Baseline (today) | Groundskeeper Agent | Change |
|---|---|---|---|
| Catch rate on corrupted examples (n=7) | 0% | 100% | +100% |
| False-flag rate on clean examples (n=11) | 0% | 0% | +0% |

## Breakdown by corruption type

| Type | Cases | Baseline caught | Agent caught |
|---|---|---|---|
| negation | 3 | 0/3 | 3/3 |
| number_swap | 4 | 0/4 | 4/4 |

## Per-example detail

| Question | Label | Type | Baseline | Agent verdict | Attempts |
|---|---|---|---|---|---|
| What is the per‑minute request limit for the Growth tier? | corrupted | number_swap | shipped | fixed | 1 |
| Which HTTP status code is returned when a client exceeds its… | corrupted | number_swap | shipped | fixed | 1 |
| To which API version do these rate limits apply? | clean | - | shipped | pass | 0 |
| What HTTP status code is returned when the daily cap is exce… | clean | - | shipped | pass | 0 |
| How long can the burst allowance be applied for? | corrupted | number_swap | shipped | fixed | 1 |
| Does burst usage count against the daily cap? | clean | - | shipped | pass | 0 |
| How many times is webhook delivery retried before it is cons… | clean | - | shipped | pass | 0 |
| What is the initial backoff interval for webhook retries, an… | clean | - | shipped | pass | 0 |
| What occurs after the webhook has been marked as failed? | corrupted | negation | shipped | fixed | 1 |
| How many paid time off (PTO) days does a full-time employee … | clean | - | shipped | pass | 0 |
| What is the maximum number of PTO days a full-time employee … | corrupted | number_swap | shipped | fixed | 1 |
| How many unused PTO days may be carried over into the follow… | clean | - | shipped | pass | 0 |
| What is the carryover limit for employees who have been with… | corrupted | negation | shipped | fixed | 1 |
| How many business days in advance must a PTO request be subm… | clean | - | shipped | pass | 0 |
| How many business days does a manager have to approve or den… | clean | - | shipped | pass | 0 |
| When are PTO requests not accepted? | clean | - | shipped | pass | 0 |
| How many sick days does each employee receive per year? | clean | - | shipped | pass | 0 |
| Do sick days carry over or get paid out upon termination? | corrupted | negation | shipped | fixed | 1 |