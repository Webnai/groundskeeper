# Evaluation Report

33 total examples (13 deliberately corrupted, 20 clean).

## Primary outcome: grounding-issue catch rate

| Metric | Baseline (today) | Groundskeeper Agent | Change |
|---|---|---|---|
| Catch rate on corrupted examples (n=13) | 0% | 100% | +100% |
| False-flag rate on clean examples (n=20) | 0% | 0% | +0% |

## Breakdown by corruption type

| Type | Cases | Baseline caught | Agent caught |
|---|---|---|---|
| number_swap | 2 | 0/2 | 2/2 |
| unrelated_answer | 11 | 0/11 | 11/11 |

## Per-example detail

| Question | Label | Type | Baseline | Agent verdict | Attempts |
|---|---|---|---|---|---|
| What is the ID of the person described in the passage? | clean | - | shipped | pass | 0 |
| What is Bhavana's occupation? | corrupted | unrelated_answer | shipped | fixed | 1 |
| Does Bhavana have kids? | corrupted | unrelated_answer | shipped | fixed | 1 |
| What is Harry's occupation? | corrupted | unrelated_answer | shipped | fixed | 1 |
| How old is Harry? | clean | - | shipped | pass | 0 |
| Does Harry have any kids? | clean | - | shipped | pass | 0 |
| What is the calmer_stressed value in the first row? | clean | - | shipped | pass | 0 |
| What is the RM_professional_growth rating for the person wit… | clean | - | shipped | pass | 0 |
| What is the occupation of Banditaa? | clean | - | shipped | pass | 0 |
| What is the occupation of the person with ID 4? | corrupted | unrelated_answer | shipped | fixed | 1 |
| According to the first line, is digital connectivity suffici… | clean | - | shipped | pass | 0 |
| In the second line, what is the calmer_stressed status? | corrupted | unrelated_answer | shipped | fixed | 1 |
| What is Ram's occupation? | corrupted | unrelated_answer | shipped | fixed | 1 |
| Does Ram have children? | clean | - | shipped | pass | 0 |
| Is digital_connect_sufficient? | clean | - | shipped | pass | 0 |
| What is Gaurav's age? | clean | - | shipped | pass | 0 |
| Does Gaurav have kids? | corrupted | unrelated_answer | shipped | fixed | 1 |
| What is the value of RM_professional_growth? | corrupted | number_swap | shipped | fixed | 1 |
| What is Sandy's occupation? | corrupted | unrelated_answer | shipped | fixed | 1 |
| What is the RM_lazy rating for Sandy? | clean | - | shipped | pass | 0 |
| Is digital connectivity sufficient according to the passage? | corrupted | unrelated_answer | shipped | fixed | 1 |
| What is Ganika's age? | clean | - | shipped | pass | 0 |
| Does Ganika have kids? | clean | - | shipped | pass | 0 |
| What is Ganika's RM_lazy rating? | clean | - | shipped | pass | 0 |
| What is Sheetal's occupation? | clean | - | shipped | pass | 0 |
| Does Sheetal have kids? | clean | - | shipped | pass | 0 |
| What rating did Sheetal give for RM_lazy? | corrupted | number_swap | shipped | fixed | 1 |
| What is Abbas's age? | clean | - | shipped | pass | 0 |
| Does Abbas have kids? | corrupted | unrelated_answer | shipped | fixed | 1 |
| What is Abbas's RM_productive rating? | clean | - | shipped | pass | 0 |
| What is the value of RM_productive? | clean | - | shipped | pass | 0 |
| Is digital_connect_sufficient sufficient? | clean | - | shipped | pass | 0 |
| Does RM have job opportunities? | corrupted | unrelated_answer | shipped | fixed | 1 |