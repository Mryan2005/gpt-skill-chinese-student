# Build a short review queue

## Use this playbook when

The user asks for `chinese-student: sort tonight` or a bounded review queue for one study
session.

## Procedure

1. Run the normal priority calculation with mode `tonight`.
2. Read the requested time budget or use the declared default in the result.
3. Select the highest-ranked cards whose estimated review cost fits the budget.
4. Keep the full score and reason data for every selected card.
5. Record excluded eligible cards and the selection reason. Do not delete them
   from the normal priority projection.
6. Keep the canonical chapter order and card order unchanged.

## Gate

The short queue is a view over the full ranking. It is not a new mastery state,
and it does not write study progress.
