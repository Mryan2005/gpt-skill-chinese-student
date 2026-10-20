---
name: exam
description: Use for a closed-book assessment against a frozen Subject snapshot. It runs the internal per-question Hit phase before isolated answering, then grades and freezes the result; do not use it for post-exam teaching or artifact repair.
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
- For every question, execute `READ_QUESTION → EXAM_HIT → INDEPENDENT_ANSWER`.
  Hit is the first formal stage of the exam, never a post-exam review step.
- The Hit Inspector and Independent Answerer use separate contexts. The
  answerer receives the original question only after Hit completes; it never
  receives card content, Hit analysis, missing-knowledge hints, or solutions.
- A pre-existing question-to-card mapping is optional. A direct mapping is a
  retrieval hint, never a gate for attempting a question.
- For every valid question, save a Hit record with required knowledge, actual
  card-content refs, missing knowledge, evidence, snapshot ID, and completion
  time. `UNRESOLVED` is a record, not a skipped question.
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
- Do not call `learn`, `study-math`, `review`, Web, or `optimize` to modify the
  tested artifact during the exam run.
- Emit an immutable Exam Result, Learning Gap Report, and Repair Requests.
  `review` consumes it for Learner Model updates; `learn` teaches remediation.
- The Exam Hit phase is an internal first stage of every question. It reads the
  frozen graph and records `HIT`, `PARTIAL`, `MISS`, or `UNRESOLVED` from actual
  card content before the Independent Answerer receives the question.

Read [exam-contract.md](references/exam-contract.md), [exam-workspace.md](references/exam-workspace.md),
[pdf-reading.md](references/pdf-reading.md), [answer-record.md](references/answer-record.md),
[grading.md](references/grading.md), [exam-phase-contract.md](references/exam-phase-contract.md),
and [error-taxonomy.md](references/error-taxonomy.md), plus the shared
[agent-role-contract.md](../../references/agent-role-contract.md).

The state machine moves forward only; rollback or first-pass overwrite is a
structure error. Hit artifacts live in the normal `.exam/current/` run.
## Routing

| User goal | Playbook |
| --- | --- |
| Start and complete a closed-book exam | [run-exam.md](playbooks/run-exam.md) |
| Grade a frozen first attempt with an explanation | [grade-exam.md](playbooks/grade-exam.md) |
| Create error categories and learning gaps | [analyze-errors.md](playbooks/analyze-errors.md) |
| Replay an exam or error history | [replay-errors.md](playbooks/replay-errors.md) |

## Done gate

Run `validate_exam_record.py`. Confirm the snapshot, state, first-pass answers,
explanation release, grading, and findings. Report Performance, Knowledge
Coverage, Graph Effectiveness, Error Profile, and Repair Requests. Route the closed Exam Result to
`review`; `exam` does not write Learner Model updates.
