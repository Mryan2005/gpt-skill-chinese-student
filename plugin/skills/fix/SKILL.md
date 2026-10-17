---
name: fix
description: Use as the write-enabled repair orchestrator for the latest valid check findings. It repairs allowed Derived, Runtime, and Generated Artifact defects without modifying Source or silently invoking relearn.
---

# 中式学生：修复入口

`fix` consumes the latest valid `check` report and repairs the reported defects.
Calling `fix` authorizes all allowed automatic repairs for that report. It does
not ask for per-finding confirmation. The user runs `check` afterward to accept
or reject the result.

## Non-negotiables

- Do not diagnose from scratch. `check` owns diagnosis and Finding evidence.
- Verify the report's run ID, artifact version, hash, and schema before writing.
- Never modify Source, original questions, official answers, official solutions,
  source quotes, original PDFs, or original images.
- Run deterministic classification and repair before semantic AI repair.
- Fixers produce Patch Proposals first. The orchestrator coordinates all writes.
- A fixer role does not require a dedicated agent thread. Capacity changes speed,
  never repair coverage.
- Every mutation maps to one or more input findings.
- Learner repairs may recalculate aggregates, indexes, mastery projections, and
  sort state, but may never rewrite historical Observations.
- Run local validation only. Do not silently run or claim a full `check`.
- Never invoke `relearn` or `update` silently. Emit `RELEARN_RECOMMENDED` or
  `REQUIRES_UPDATE` instead.
- Stop on a stale report, source blockage, destructive escalation, unresolved
  write conflict, or repeated no-progress rounds.

Read [fix-contract.md](references/fix-contract.md),
[repair-plan-schema.md](references/repair-plan-schema.md),
[patch-proposal-schema.md](references/patch-proposal-schema.md), and
[conflict-policy.md](references/conflict-policy.md).

## Routing

| User goal | Playbook |
| --- | --- |
| Repair the latest check report | [fix-from-report.md](playbooks/fix-from-report.md) |
| Repair schema, IDs, or generated fields | [schema-fix.md](playbooks/schema-fix.md) |
| Repair provenance and source links | [provenance-fix.md](playbooks/provenance-fix.md) |
| Repair question mappings | [question-fix.md](playbooks/question-fix.md) |
| Repair answers and derived solutions | [solution-fix.md](playbooks/solution-fix.md) |
| Repair graph relations | [relation-fix.md](playbooks/relation-fix.md) |
| Repair formula markup | [latex-fix.md](playbooks/latex-fix.md) |
| Repair runtime and generated output | [runtime-fix.md](playbooks/runtime-fix.md) |
| Repair learner state projection | [learner-state-fix.md](playbooks/learner-state-fix.md) |

## State machine

~~~text
NEW_FIX_REQUEST
→ RESET_FIX_WORKSPACE
→ LOAD_CHECK_REPORT
→ VERIFY_REPORT_FRESHNESS
→ BUILD_REPAIR_PLAN
→ SNAPSHOT_CURRENT_STATE
→ ANALYZE_PROPOSALS
→ MERGE_PROPOSALS
→ APPLY_PATCHES_BY_PHASE
→ LOCAL_VALIDATE
→ WRITE_FIX_REPORT
→ CLOSED
~~~

## Done gate

Write a `fix.report.v1` report with resolved, remaining, blocked, changes,
execution mode, local validation, and escalation fields. End with `请运行 check
验收当前结果。` Do not claim full-audit success inside `fix`.
