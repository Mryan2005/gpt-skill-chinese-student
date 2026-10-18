# Exam postmortem

Use this playbook after `exam` has closed a run and frozen its first-pass
answers.

## Procedure

1. Load the immutable Exam Result and verify `examRunId`, `attemptId` values,
   artifact version, artifact hash, and `answersFrozen`.
2. Calculate the independent completeness dimensions. Keep total questions,
   attempted questions, scored questions, unanswered questions, ungraded
   questions, unreadable questions, and invalid questions separate.
3. Build one diagnosis for every question. Preserve the observed outcome even
   when no diagnosis is possible.
4. Use `primaryCardId`, `secondaryCardIds`, and typed relations to create
   separate Knowledge Mastery and Question Mastery assessments.
5. Mark a cause as confirmed only when the Exam Result contains direct
   evidence. Otherwise write a bounded hypothesis or `unknown`.
6. Create `learningTasks` with dependencies and acceptance criteria. Create a
   `retestPlan` for every mastery gap that needs verification.
7. Compare prior immutable attempts only when difficulty, coverage, conditions,
   and sample size are comparable. Otherwise report insufficient evidence.
8. Apply the review report through `apply_review_update.py`. Existing
   idempotency keys must be skipped, not counted again.
9. Validate the updated observation records and write `review.report.v2`.

## Routing

- Send learner-performance tasks to `sort`, then `learn`.
- Send official-answer, solution, or provenance conflicts to `amend`.
- Send question, mapping, formula, renderer, or graph defects to
  `check`/`fix`/`heal`.
- Do not modify the Exam Result or the learning artifact in this playbook.

## Completion

The report must explain the evidence gap when it cannot determine why an answer
was wrong. A correct answer without independent transfer evidence remains below
`verified`. An unanswered question remains unassessed.
