---
name: amend
description: Use when the user explicitly reports missing, incorrect, unclear, outdated, or poorly structured learning content and asks to supplement or correct it. Apply the smallest coherent change to the affected writable layer and run local validation without requiring a prior check report.
---

# Amend

`amend` is the User-Directed Supplement and Correction Runner. The user's
feedback is the input authority for the requested amendment. `amend` interprets
the feedback, locates the affected model layer, applies a coherent correction or
supplement, and validates the affected area.

## Boundaries

- `learn` builds from new material. `amend` changes an existing learning
  artifact because the user identified a specific problem or omission.
- `fix` consumes a current `check` report. `amend` does not need a check report
  when the user's feedback is specific enough to act on.
- `heal` owns repeated `check` and `fix` convergence. `amend` performs one
  user-directed change and stops after local validation.
- `profile` records what the user says about their own learning. `amend` records
  what the user says is wrong or missing in the learning artifact.
- `relearn` and `update` remain explicit escalation paths. Never invoke either
  one silently.

## Non-negotiables

- Treat the user's stated request as `source: "user_feedback"` and preserve its
  exact wording in the amendment record.
- Do not mechanically replace text. Trace the request to the affected Card,
  Question, Solution, Relation, transcription record, runtime artifact, or
  Learner Model layer before writing.
- Never overwrite original images, PDFs, questions, official answers, official
  solutions, or Source Records. Record user corrections as new provenance.
- If the user disputes an official answer, preserve the official value and add a
  user correction, derived value, and explicit conflict status.
- If a transcription is wrong, keep the original Source and revise only the
  structured transcription or Derived record with correction provenance.
- Preserve historical Observations. A Learner Model amendment may append user
  correction evidence and adjust a derived aggregate, but it cannot rewrite the
  observed event.
- Do not run a full `check` automatically. Run only targeted JSON/schema,
  reference, LaTeX, JavaScript, relation, or question-mapping validators that
  cover the changed layers.
- Stop with `NEEDS_CLARIFICATION`, `RELEARN_REQUIRED`, `UPDATE_REQUIRED`, or
  `BLOCKED_BY_SOURCE` when a safe local amendment is not possible.

## Workflow

~~~text
USER_FEEDBACK
→ PARSE_REQUEST
→ LOCATE_TARGETS
→ WRITE_AMENDMENT_PLAN
→ APPLY_MINIMAL_COHERENT_CHANGE
→ RUN_LOCAL_VALIDATORS
→ WRITE_AMENDMENT_RECORD
→ REPORT
~~~

Read [amend-contract.md](references/amend-contract.md) before changing an
artifact. Write an `amend.report.v1` report and validate it with
[validate_amend_report.py](scripts/validate_amend_report.py). Tell the user to
run `check` for full acceptance or `heal` for repeated repair.
