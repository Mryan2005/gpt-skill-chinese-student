---
name: exam
description: Use as the closed-book assessment runner for a frozen Subject snapshot. It records first-pass answers, releases solutions only after freezing, grades performance, and produces learning-gap reports without modifying the learning artifact.
---

# Exam

`exam` measures performance against a frozen knowledge state. It does not build
knowledge, define card semantics, or audit Subject quality.

## Non-negotiables

- Freeze the Subject snapshot before measurement.
- Delete and recreate `.exam/current/` before every new exam. Verify the clean
  workspace before loading the new paper.
- Read the original exam and explanation PDFs directly. Do not use OCR, OCR
  packages, external OCR APIs, transcript substitutes, or delegated OCR.
- During `FIRST_PASS`, access only the frozen graph and questions.
- A pre-existing question-to-card mapping is optional. A direct mapping is a
  retrieval hint, never a gate for attempting a question.
- For every readable question, interpret the question and attempt retrieval
  across the frozen Subject. Record the actual cards and evidence used.
- Give every question an explicit `attemptStatus` and retrieval record before
  freezing answers. Unprocessed questions block `ANSWERS_FROZEN`.
- During the first pass, do not use the Web, explanations, answer keys, other
  materials, or knowledge added after the snapshot.
- The Learner Model may guide coverage or difficulty before the snapshot is
  frozen. It must not provide hints or personalized cues after
  `SNAPSHOT_FROZEN`.
- Save and freeze first-pass answers before releasing explanations. Append
  revisions after the freeze. Never overwrite the first attempt.
- Release explanations, grade, and analyze errors only after answers are frozen.
- Do not call `learn`, `study-math`, or `review` to modify the tested artifact
  during the exam run.
- Emit an immutable Exam Result, Learning Gap Report, and Repair Requests.
  `review` consumes it for Learner Model updates; `learn` teaches remediation.
- `exam hit` is a separate read-only coverage audit: it reads every question
  against one frozen graph snapshot and records `HIT`, `PARTIAL`, `MISS`, or
  `UNRESOLVED` from actual card content. It never changes the Exam Result or
  Learner Model.

Read [exam-contract.md](references/exam-contract.md), [exam-workspace.md](references/exam-workspace.md),
[pdf-reading.md](references/pdf-reading.md), [answer-record.md](references/answer-record.md),
[grading.md](references/grading.md), [hit-contract.md](references/hit-contract.md),
and [error-taxonomy.md](references/error-taxonomy.md).

The state machine moves forward only; rollback or first-pass overwrite is a
structure error. `exam hit` has its own disposable `.exam-hit/current/` run.
## Routing

| User goal | Playbook |
| --- | --- |
| Start and complete a closed-book exam | [run-exam.md](playbooks/run-exam.md) |
| Grade a frozen first attempt with an explanation | [grade-exam.md](playbooks/grade-exam.md) |
| Create error categories and learning gaps | [analyze-errors.md](playbooks/analyze-errors.md) |
| Replay an exam or error history | [replay-errors.md](playbooks/replay-errors.md) |
| Test graph coverage against every question | [hit.md](playbooks/hit.md) |

## Done gate

Run `validate_exam_record.py`. Confirm the snapshot, state, first-pass answers,
explanation release, grading, and findings. Report Performance, Knowledge
Coverage, Graph Effectiveness, Error Profile, and Repair Requests. Route the closed Exam Result to
`review`; `exam` does not write Learner Model updates.
