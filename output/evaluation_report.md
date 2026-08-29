# Evaluation Report

18 total examples (7 deliberately corrupted, 11 clean).

## Primary outcome: grounding-issue catch rate

| Metric | Baseline (today) | Groundskeeper Agent | Change |
|---|---|---|---|
| Catch rate on corrupted examples (n=7) | 14% | 100% | +86% |
| False-flag rate on clean examples (n=11) | 0% | 0% | +0% |

## Breakdown by corruption type

| Type | Cases | Baseline caught | Agent caught |
|---|---|---|---|
| negation | 2 | 0/2 | 2/2 |
| number_swap | 4 | 0/4 | 4/4 |
| unrelated_answer | 1 | 1/1 | 1/1 |

## Per-example detail

| Question | Label | Type | Baseline | Agent verdict | Attempts |
|---|---|---|---|---|---|
| What is the per‑minute request limit for the Growth tier? | corrupted | number_swap | shipped | fixed | 1 |
| How many daily requests are allowed for the Free tier? | corrupted | number_swap | shipped | fixed | 1 |
| What HTTP status code does the API return when a client exce… | clean | - | shipped | pass | 0 |
| What HTTP status code is returned when the daily cap is exce… | clean | - | shipped | pass | 0 |
| How long does the burst allowance last and what percentage o… | corrupted | number_swap | shipped | fixed | 1 |
| What happens to free tier accounts that exceed the daily cap… | clean | - | shipped | pass | 0 |
| How many times is webhook delivery retried according to the … | clean | - | shipped | pass | 0 |
| What is the initial backoff interval for webhook retries? | clean | - | shipped | pass | 0 |
| How is the customer notified after a webhook is marked as fa… | corrupted | unrelated_answer | flagged | duplicate | 0 |
| What is the paid time off (PTO) accrual rate for full-time e… | clean | - | shipped | pass | 0 |
| How many unused PTO days may be carried over into the follow… | corrupted | number_swap | shipped | fixed | 1 |
| When are unused PTO days beyond the carryover cap forfeited? | clean | - | shipped | pass | 0 |
| What is the carryover policy for employees who have been wit… | corrupted | negation | shipped | fixed | 1 |
| How many business days in advance must a PTO request be subm… | clean | - | shipped | pass | 0 |
| How long does a manager have to approve or deny a PTO reques… | clean | - | shipped | pass | 0 |
| When are PTO requests not accepted? | clean | - | shipped | pass | 0 |
| How many sick days does each employee receive per year? | clean | - | shipped | pass | 0 |
| Do sick days carry over to the next year or get paid out upo… | corrupted | negation | shipped | fixed | 1 |