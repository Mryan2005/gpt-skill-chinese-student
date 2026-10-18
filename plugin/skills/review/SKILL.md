---
name: review
description: Use after a closed-book exam to produce evidence-based diagnoses, separate knowledge and question mastery, create learning and retest tasks, update the local Learner Model idempotently, and track progress across attempts without changing the learning artifact.
---

# Review

`review` is the evidence-based Exam Result postmortem. It answers why an
attempt failed, what is actually unsupported, what to learn next, how to test
the gap, and whether later evidence proves improvement.

`exam` measures and freezes evidence. `review` interprets it. `learn` executes
the remediation. `sort` consumes the updated evidence. `amend` handles content
conflicts, while `check`, `fix`, and `heal` handle artifact defects.

## Non-negotiables

- Consume only a closed Exam Result with immutable first-pass answers, grading
  evidence, artifact identity, and question-level provenance.
- Preserve distinct outcomes: `correct`, `incorrect`, `partially_correct`,
  `unanswered`, `unreadable`, `ungraded`, and `invalid`.
- Keep confirmed diagnosis separate from hypotheses. Use `unknown` when the
  evidence cannot support a cause. Never invent an unobserved reasoning step.
- Keep Knowledge Mastery and Question Mastery in separate structures.
- Do not treat one correct answer as `verified`, one wrong answer as total
  ignorance, or an unanswered question as an error.
- Generate concrete `learningTasks` and `retestPlans`, each with evidence,
  target IDs, success criteria, and a verification rule.
- Append factual exam observations idempotently. The same `attemptId` and
  `diagnosticVersion` must never increment state twice.
- Never mutate the Exam Result, first-pass answer, Source, official answer,
  official solution, canonical knowledge, HTML, or user self-report.
- Route content conflicts to `amend` and artifact defects to `check`, `fix`, or
  `heal`. A student mistake alone is not an artifact defect.
- Run local Learner Model validation only. Do not run a full `check` silently.

Run [postmortem.md](playbooks/postmortem.md) for the standard workflow and read
[review-contract.md](references/review-contract.md) before processing an Exam
Result. Validate the output with
[validate_review_report.py](scripts/validate_review_report.py). Apply local
observation updates with
[apply_review_update.py](scripts/apply_review_update.py); the script is
idempotent and requires `--apply` before writing.

## State machine

~~~text
NEW_REVIEW_REQUEST
→ LOAD_CLOSED_EXAM_RESULT
→ VERIFY_FROZEN_ATTEMPTS_AND_ARTIFACT_IDENTITY
→ CLASSIFY_OUTCOME_AND_ERROR_EVIDENCE
→ ASSESS_KNOWLEDGE_AND_QUESTION_MASTERY
→ BUILD_LEARNING_TASKS_AND_RETEST_PLANS
→ COMPARE_HISTORY
→ APPLY_IDEMPOTENT_LEARNER_UPDATE
→ WRITE_REVIEW_REPORT
→ CLOSED
~~~

## Done gate

Write `review.report.v2` with completeness dimensions, question-level
diagnoses, evidence references, uncertainty, separate mastery changes,
learning tasks, retest plans, historical progress, routing, and downstream
handoff data. The report must state that the Exam Result and artifact were not
mutated.
