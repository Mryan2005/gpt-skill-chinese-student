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
- Do not rerun the exam, solve a question again, regrade, reread PDFs, remap
  graph links, audit Source, or repair any artifact. Those actions belong to
  `exam`, `check`, `fix`, `amend`, or `heal`.
- Reset and verify `.review/current/` before processing. Read the Exam Result
  from `.exam/` or the project's equivalent closed-result path; never delete
  the Exam workspace.
- Hash the Exam Result before and after review. A mismatch is
  `REVIEW_MUTATED_EXAM_RESULT` and fails the run.
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
- Apply the Learner Attribution Gate per question. Artifact, Source, grading,
  conflict, ungraded, and non-learner attempt blockers cannot create learner
  evidence.
- Never mutate the Exam Result, first-pass answer, Source, official answer,
  official solution, canonical knowledge, HTML, or user self-report.
- Route content conflicts to `amend` and artifact defects to `check`, `fix`, or
  `heal`. A student mistake alone is not an artifact defect.
- Run local Learner Model validation only. Do not run a full `check` silently.

Run [postmortem.md](playbooks/postmortem.md) for the standard workflow,
[reset_review_workspace.py](scripts/reset_review_workspace.py) before a new
run, and [validate_exam_result.py](scripts/validate_exam_result.py) before
diagnosis. Read [review-contract.md](references/review-contract.md) before
processing an Exam Result. Validate the output with
[validate_review_report.py](scripts/validate_review_report.py). Apply local
observation updates with
[apply_review_update.py](scripts/apply_review_update.py); the script is
idempotent and requires `--apply` before writing.
Validate overlays with [validate_annotations.py](scripts/validate_annotations.py)
and render them for Markdown or Site consumers with
[render_annotations.py](scripts/render_annotations.py). Rendering never edits
the original Source.
## Review modes

`Learner Review` requires reliable human evidence before writing user mastery.
`Material Review` processes any reliable Exam Result without updating the user's
Learner Model. Use [material_review.py](scripts/material_review.py) and
[validate_material_review.py](scripts/validate_material_review.py) for that path.

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
