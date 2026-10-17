# Build a review-priority queue

## Use this playbook when

The user asks which existing cards deserve attention first, or asks for a
review order without naming a special mode.

## Procedure

1. Load the current Subject artifact and its domain contract.
2. Load the learner state, closed exam gap reports, and current check findings.
3. Reject or mark stale any signal whose artifact version does not match the
   current Subject.
4. Build one signal row for every eligible card. Use `null` for an unknown
   signal. Do not use zero as a placeholder for missing evidence.
5. Apply the selected profile from [modes.md](../references/modes.md). Record
   the exact weights in the result.
6. Calculate the normalized score over known dimensions. Record confidence as
   the fraction of weight supported by known signals.
7. Attach reason codes and evidence to each ranked card.
8. Sort by descending score, then descending confidence, then ascending card ID.
9. Write the review-priority projection without changing the canonical card
   order or card content.
10. Validate the result with `validate_priority.py`.

## Gate

The output explains why a card is early in the queue. It does not claim that
the card is correct, mastered, or more important than a domain contract says.
