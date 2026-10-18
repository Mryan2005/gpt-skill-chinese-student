---
name: review
description: Use after a closed-book exam to process its structured Exam Result, diagnose why answers failed, update the local Learner Model, and produce remediation and routing plans without modifying the learning artifact.
---

# Review

`review` is the Exam Result Postmortem and Learning Feedback Processor. It
consumes a frozen, graded `ExamResult`; it does not read the exam PDF as its
primary input, reteach the user, or repair the Subject artifact.

## Non-negotiables

- Consume only a closed Exam Result with frozen first-pass answers, grading
  evidence, artifact version, and question-level provenance.
- Classify the failure stage and reason from evidence. Use the domain taxonomy
  for domain-specific subtypes.
- Separate learner problems from content problems and system problems.
- For a learner problem, append a factual Observation and update derived Error
  Model, Mastery, or Explanation Model through the Learner Model contract.
- Never rewrite historical Observations, first-pass answers, official answers,
  official solutions, Source, cards, questions, relations, Markdown, or HTML.
- Route content problems to `amend`. Route structural or runtime problems to
  `check`, `fix`, or `heal`. Do not repair those artifacts inside `review`.
- Do not teach during review. Produce a remediation plan for `learn` and a
  review-priority update for `sort`.
- Preserve disagreement between official, historical, derived, and user
  evidence. A wrong answer does not prove that a knowledge card is wrong.
- Review writes only local Learner Model state and the review report. It does
  not run a full `check` automatically.

Read [review-contract.md](references/review-contract.md) before processing an
Exam Result. Validate the output with
[validate_review_report.py](scripts/validate_review_report.py).

## Routing

| Finding | Route |
| --- | --- |
| Retrieval, method, condition, execution, memory, or time problem | Learner Model, then `sort` and `learn` |
| Official answer or explanation conflict | `amend` with preserved official provenance |
| Question, Source, mapping, or knowledge artifact defect | `check`, `fix`, or `heal` |
| Incomplete evidence or ambiguous diagnosis | `BLOCKED` or `NEEDS_REVIEW` |

## State machine

~~~text
NEW_REVIEW_REQUEST
→ LOAD_CLOSED_EXAM_RESULT
→ VERIFY_RESULT_FRESHNESS
→ CLASSIFY_QUESTION_ERRORS
→ SEPARATE_LEARNER_CONTENT_SYSTEM_PROBLEMS
→ APPEND_LEARNER_EVIDENCE
→ BUILD_REMEDIATION_PLAN
→ WRITE_REVIEW_REPORT
→ CLOSED
~~~

## Done gate

Write a `review.report.v1` report with question-level diagnoses, evidence,
Learner Model updates, routing decisions, remediation cards and strategies,
local validation, and next actions for `sort` and `learn`. The report must
state that the Exam Result and learning artifact were not mutated.
