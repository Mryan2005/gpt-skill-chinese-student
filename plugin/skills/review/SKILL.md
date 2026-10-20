---
name: review
description: Use after a frozen exam or explicit user-written submission to review evidence, highlight knowledge, diagnose eligible learner gaps, and plan learning. It consumes results; it does not run a new exam, audit the graph, or repair artifacts.
---

# Review

`review` is the evidence-based Exam Result postmortem. It answers why an
attempt failed, what is actually unsupported, what to learn next, how to test
the gap, and whether later evidence proves improvement.

`exam` measures and freezes evidence. `review` interprets it. `learn` executes
the remediation. `sort` consumes the updated evidence. `amend` handles content
conflicts, while `check`, `fix`, and `heal` handle artifact defects.

Every mode consumes `PDF → Exam Hit → highlight → gap detection → research → learn handoff → recheck → report`. Exam-result reads frozen per-question Hit records; user-written may delegate a Hit Inspector only when no Exam-generated Hit exists.

## Non-negotiables

- Consume only a closed Exam Result with immutable first-pass answers, grading
  evidence, artifact identity, and question-level provenance.
- Do not rerun the exam, re-answer, regrade, remap graph links, audit Source,
  or repair any artifact. Review must directly read the original PDFs with
  native PDF/page capability and must never use OCR or a surrogate transcript.
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
- Consume a complete per-question Exam Hit record from the frozen Exam Result;
  do not recompute or overwrite it in `exam-result` mode.
- Keep original hits separate from `enriched_exam_coverage`; external research
  is an `External Supplement`, never an official answer or Source replacement.

Run [exam-result.md](playbooks/exam-result.md) by default, or
[user-written.md](playbooks/user-written.md) only after explicit user-submission
intent. Read [review-contract.md](references/review-contract.md) before review.
Read [agent-role-contract.md](../../references/agent-role-contract.md) before
splitting review work.
Reset with [reset_review_workspace.py](scripts/reset_review_workspace.py),
validate with [validate_review_report.py](scripts/validate_review_report.py),
and apply observations only through the idempotent
[apply_review_update.py](scripts/apply_review_update.py) `--apply` gate.
Validate overlays with [validate_annotations.py](scripts/validate_annotations.py);
compose Hit with [compose_hit_review.py](scripts/compose_hit_review.py), then validate with [validate_hit_review.py](scripts/validate_hit_review.py).
Rendering never edits Source.
## Review modes

`review` defaults to `exam-result`; `review user-written` requires explicit
human-submission intent and a new `attemptId`. `exam-result` runs Material
Review for any answerer, then runs Learner Review only for eligible human
evidence. `user-written` directly reads questions, answers, and the user's PDF
submission and may update Learner State only from verified human evidence.
Both modes produce structured/Markdown/HTML review outputs and never generate
PDF. Use [material-review.md](playbooks/material-review.md),
[exam-hit-enrichment.md](playbooks/exam-hit-enrichment.md),
[material_review.py](scripts/material_review.py),
[route_review.py](scripts/route_review.py), and
[validate_review_mode.py](scripts/validate_review_mode.py).

The review state machine is: route → read original PDFs → consume/delegate Hit →
highlight and classify gaps → research/learn handoff → recheck → Learner Review
update → report. It never calls `heal` recursively.

## Done gate

Write `review.report.v2` with completeness dimensions, question-level
diagnoses, evidence references, uncertainty, separate mastery changes,
learning tasks, retest plans, historical progress, routing, and downstream
handoff data. The report must state that the Exam Result and artifact were not
mutated.
