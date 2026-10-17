# Sort contract

`sort` owns a review-priority projection. The Subject and its domain model own
the learning content.

## Inputs

- the current canonical cards, questions, relations, and source references;
- the selected domain contract and its importance or frequency signals;
- the local Learner Model: explicit self-report claims, Error Model, Explanation
  Model, Observations, Mastery, and the current learning epoch;
- the current closed `exam` result, or an exam-gap record already accepted by
  `learn` into the learner state;
- current `check` findings for the same artifact version;
- the requested mode and optional session budget.

Every input records its path, version, and observation time in the output. A
signal from an older artifact is stale. The sorter excludes it or marks it as
stale instead of mixing it with current state. It never treats a disposable
`.exam/current` file from an earlier run as exam history.

## Allowed output

`sort` may replace `.local/learner/subjects/<subject-id>/sort-state.json` and
the review-priority projection for the current Subject. The
projection may contain:

- `priority_score` and its dimension breakdown;
- `priority_reason` objects with evidence;
- a stable `review_order`;
- a bounded `review_queue` and excluded-card explanations;
- the mode, weights, confidence, and input versions.

The projection is a view. It is not a second copy of card content.

Self-reported weaknesses may seed `user_weakness` when behavioral evidence is
not yet sufficient. Store the claim path and ID as evidence, label the reason
`self_reported_weakness`, and give repeated observed errors or mastery evidence
precedence when signals conflict. Explanation preferences affect how a review
is presented, not whether a card is factually correct.

## Forbidden writes

Do not change Source, Derived card text, definitions, formulas, solutions,
questions, relations, canonical Markdown, HTML, canonical `learner_state`, or
the canonical chapter order. Do not resolve a check finding or invent a domain
importance value. The local sort projection is the only Learner-layer write.

## Scoring and missing signals

Each dimension is normalized to 0 through 100 or set to `null`. The score is a
weighted mean over known dimensions:

~~~text
score = sum(weight × known value) / sum(weight for known dimensions)
~~~

When every dimension is unknown, set `score=null`, `confidence=0`, and
`status=insufficient-signal`. Never turn missing evidence into a low score.

## Stable ordering

Sort ranked cards by descending score, descending confidence, and ascending
card ID. Use the same rule for every run with the same inputs and mode.

## Safety

Sorting is reversible and idempotent. A new run replaces only the projection.
The operation never needs destructive confirmation.
