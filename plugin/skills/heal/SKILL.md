---
name: heal
description: Use as the iterative check-fix convergence loop for learning artifacts when one check and one fix are not enough. Reuse isolated Checker and Fixer roles, re-check after every repair, and stop safely on convergence, no progress, regressions, blockers, or the ten-round limit.
---

# 中式学生：检查—修复闭环

`heal` is orchestration. It repeatedly invokes the existing `check` and `fix`
contracts; it does not create a second audit system or a second repair system.
One round is exactly one fresh check followed by at most one fix.

## Non-negotiables

- The Checker is read-only. It may inspect Source, Derived, Learner Model,
  validators, HTML, and current generated artifacts, but it never edits them.
- The Fixer is write-enabled only within the existing `fix` contract. It may
  consume the current round's findings, but it may not redefine the diagnosis.
- Reuse one Checker role and one Fixer role for the whole run. Agent capacity
  changes execution mode, not audit scope or repair scope.
- Reset and verify `.heal/current/` before loading the current artifact. Keep
  checker, fixer, and state files isolated inside that workspace.
- Every fix must be followed by a fresh check against the current artifact.
  Previous findings are for progress comparison only, never current truth.
- Never invoke `relearn` or duplicate `update` inside the loop. Emit
  `RELEARN_REQUIRED` or `UPDATE_REQUIRED` and stop.
- Preserve Source and official material. A missing or corrupted required Source
  is a blocker, not an invitation to guess or fabricate.
- Use at most 10 repair rounds, then run one final check. Warnings may remain
  when blocker and error counts are zero and no auto-fixable issue remains.

Read [heal-contract.md](references/heal-contract.md) before running the loop
and [run-state.md](references/run-state.md) when writing the progress report.
Use [reset_heal_workspace.py](scripts/reset_heal_workspace.py) to reset the
disposable workspace and [validate_heal_report.py](scripts/validate_heal_report.py)
to validate the final report.

## State machine

~~~text
NEW_HEAL_REQUEST
→ RESET_HEAL_WORKSPACE
→ WORKSPACE_VERIFIED_CLEAN
→ LOAD_CURRENT_ARTIFACT
→ REUSE_CHECKER_AND_FIXER
→ CHECK_CURRENT_ARTIFACT
→ EVALUATE_STOP_CONDITIONS
├─ PASS / acceptable PASS_WITH_WARNINGS → SUCCESS
├─ unfixable blocker / escalation → STOP_BLOCKED
├─ no progress / regression → STOPPED
└─ fixable FAIL → FIX_CURRENT_FINDINGS
                → LOCAL_VALIDATE
                → CHECK_CURRENT_ARTIFACT
                → ...
→ FINAL_CHECK
→ REPORT
→ CLOSED
~~~

## Done gate

Write a `heal.report.v1` report containing every check/fix round, artifact
hashes, finding fingerprints, resolved/persisted/new/regressed counts, local
validation, stop reason, and the final check. Never report success from a fixer
claim alone.
