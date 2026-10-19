# Exam-driven contract

`heal.exam-driven.report.v1` is a coordinator report, not an Exam Result and
not a Learner Model update. It uses the same at-most-five-round protocol as
default `heal`.

Every run must consume a complete `exam.hit.report.v1` baseline. Hit is a
question-by-question content test, not a question-mapping count or an answer
performance score. Each repair round produces a new graph snapshot and a new
Hit report before comparing coverage.

Required evidence includes:

- original PDF provenance and native-reading status;
- baseline metrics with readable, blocked, mapped, solution, formula, source,
  and retrieval counts;
- immutable iteration/holdout question IDs;
- the non-consuming read-only check before and after every round;
- the Hit baseline and the new Hit report after each repair;
- every round's evaluation, diagnosis, repair owner, repair result, one
  `optimize` phase (including an explicit no-op), regression result, coverage
  and quality deltas, stability result, and evidence references;
- explicit stop reason and final status.

Allowed repair owners are `check`, `fix`, `learn`, and `amend`. A repair may
not modify the original PDF, Source, frozen Exam Result, or Learner State.

`heal exam` may use a trustworthy web source only as an explicitly recorded
External Supplement. It cannot replace the original PDF, manufacture a missing
answer, or bypass `optimize`/`check`.

Answer text alone is never a valid knowledge repair. A question may be marked
`ANSWER_OVERFIT_RISK` when performance improves without coverage, mapping,
solution, or holdout improvement.
