---
name: heal
description: Use as the learning-experience optimizer for a learning artifact. Run a fresh cold-start novice through the user-facing study path, record learning friction, let a maintainer evaluate it, repair only validated problems, and repeat with a new novice for at most ten rounds.
---

# Heal

`heal` tests whether the artifact can teach a first-time learner. It creates a
fresh cold-start Novice Learner for each round, records the learner's path and
friction, and gives that evidence to a Maintainer. The Maintainer checks the
feedback against Source, domain contracts, schemas, mappings, relations, and
the existing `check` and `fix` contracts before making a repair.

`check` and `fix` remain available as technical verification and repair tools.
They do not replace the novice learning trace.

## Non-negotiables

- The Novice Learner is read-only and cold-start. It may see only the normal
  user-facing learning artifact, navigation, search, and question bank.
- The Novice Learner must not read Source provenance, code, schemas, validators,
  `.check/`, `.fix/`, previous heal rounds, or the user's Learner Model.
- Create a genuinely fresh novice context for every round. Never reuse a novice
  that has already learned the subject.
- The Novice Learner may use no outside knowledge to fill a gap. It records the
  friction, then continues learning through the full path.
- Synthetic novice traces are not user evidence. Never write them to
  `.local/learner/`.
- The Maintainer is independent from the novice. It may read Source, domain
  contracts, schemas, validators, current artifacts, and the trace. It decides
  `ACCEPT`, `REFINE`, `REJECT`, or `BLOCKED` for each friction finding.
- Only validated Maintainer repairs may write Derived, Runtime, or generated
  artifacts. Source and official provenance remain immutable.
- Reset and verify `.heal/current/` before loading the current artifact. Keep
  each round's learner trace and maintainer report isolated inside that
  workspace.
- Every repair must be followed by local validation. A later fresh novice must
  learn the changed artifact; previous friction is comparison data only.
- Never invoke `relearn` or duplicate `update` inside the loop. Emit
  `RELEARN_REQUIRED` or `UPDATE_REQUIRED` and stop.
- Preserve Source and official material. A missing or corrupted required Source
  is a blocker, not an invitation to guess or fabricate.
- Use at most 10 rounds. Stop on pedagogical convergence, two rounds with no
  meaningful friction reduction, unsafe regressions, a blocker, or the limit.

Read [heal-contract.md](references/heal-contract.md) and
[run-state.md](references/run-state.md) before running the loop. Use
[validate_learning_trace.py](scripts/validate_learning_trace.py) for synthetic
trace records and [validate_heal_report.py](scripts/validate_heal_report.py)
for the final report.
Use [reset_heal_workspace.py](scripts/reset_heal_workspace.py) to reset the
disposable workspace and [validate_heal_report.py](scripts/validate_heal_report.py)
to validate the final report.

## State machine

~~~text
NEW_HEAL_REQUEST
→ RESET_HEAL_WORKSPACE
→ WORKSPACE_VERIFIED_CLEAN
→ LOAD_CURRENT_ARTIFACT
→ FRESH_COLD_START_NOVICE
→ LEARN_USER_FACING_PATH
→ RECORD_LEARNING_FRICTION
→ MAINTAINER_EVALUATION
├─ ACCEPT / REFINE → REPAIR
├─ REJECT → KEEP_TRACE_ONLY
├─ BLOCKED → STOP_BLOCKED
└─ no pedagogical progress → STOP_STALLED
→ LOCAL_VALIDATE
→ NEXT_FRESH_NOVICE
→ ...
→ PEDAGOGICAL_FINAL_EVALUATION
→ REPORT
→ CLOSED
~~~

## Done gate

Write a `heal.report.v2` report containing every novice trace, friction
fingerprint, Maintainer decision, repair, learning-progress summary, local
validation, and stop reason. Report `HEALED`, `HEALED_WITH_WARNINGS`,
`STALLED`, `BLOCKED`, or `MAX_ROUNDS_REACHED`; do not report success from a
technical check or Maintainer claim alone.
