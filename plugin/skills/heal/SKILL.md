---
name: heal
description: Use for a bounded novice-experience or exam-driven improvement loop that routes evidence to existing skills. It is not a general repair shortcut, exam runner, or destructive rebuild, and never mutates real Learner State.
---

# Heal

Default `heal` runs a fresh cold-start Novice Learner through the user-facing
artifact. An independent Maintainer evaluates friction and only validated
repairs are applied.

`heal exam` (alias `exam-driven`) reuses the Exam-internal Hit phase on the complete uploaded
exam PDF against one frozen graph snapshot, evaluates knowledge coverage, keeps iteration and holdout questions separate, and routes repairs to
`check`/`fix`/`learn`/`amend`, and re-evaluates. It never updates Learner State,
rewrites Source, or repairs by inserting a tested answer into a card.

## Non-negotiables

- The default Novice Learner is fresh, read-only, uses no outside knowledge,
  and never reads Source, code, prior rounds, or real Learner Model.
- Synthetic traces are not learner evidence. Maintainer decisions are
  independent and must be checked against Source, schemas, domain contracts,
  mappings, relations, and existing check/fix contracts.
- Source, official provenance, frozen Exam Results, and real Learner State are
  immutable in every mode.
- Reset and verify `.heal/current/`; isolate every round and validate every
  repair. Never invoke `relearn` or duplicate `update` inside a loop.
- Use at most 5 repair rounds. Each round is
  `check → fix/learn → optimize → check`; the initial and final read-only
  checks do not consume rounds. Stop on convergence, no progress, regression,
  optimization oscillation, blocker, evidence/permission blockage, or the
  limit. Five rounds is not success.
- Call the existing `$chinese-student:optimize` Skill at most once per round. A no-op is still
  recorded, and opposite merge/split proposals without new evidence stop the
  loop.
- Exam PDFs are read directly by the model/page reader. OCR, OCR transcripts,
  web answers, and delegated OCR are prohibited.

Read [heal-contract.md](references/heal-contract.md) and
[run-state.md](references/run-state.md) for the default loop. For
exam-driven, read [exam-driven.md](playbooks/exam-driven.md) and
[exam-driven-contract.md](references/exam-driven-contract.md).
Use [reset_heal_workspace.py](scripts/reset_heal_workspace.py),
[validate_heal_report.py](scripts/validate_heal_report.py),
[validate_learning_trace.py](scripts/validate_learning_trace.py),
[run_exam_driven.py](scripts/run_exam_driven.py), and
[validate_exam_driven_report.py](scripts/validate_exam_driven_report.py).

## Routing

`heal` coordinates evaluation, diagnosis, repair routing, re-evaluation, graph
optimization, and stop decisions. It does not reimplement `check`, `fix`,
`learn`, `amend`, or `optimize`.

For `heal exam` / `exam-driven`, the same five-round protocol applies. The
original PDF remains authoritative; optional web research is only an explicitly
provenanced External Supplement and never replaces the PDF or inserts answers.

## Done gate

Default mode writes `heal.report.v2` with novice traces, Maintainer decisions,
repairs, validation, and stop reason. `exam-driven` writes
`heal.exam-driven.report.v1` with PDF provenance, baseline, iteration/holdout
split, round metrics, repair owners, regression checks, and stop reason.
Report `HEALED`, `PARTIAL`, `STALLED`, `BLOCKED`, or `MAX_ROUNDS_REACHED`; do
not report success from a technical check or Maintainer claim alone.
