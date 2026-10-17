# Full audit

## Use this playbook when

Use it when the user asks to check a whole Subject or the scope is not narrow
enough for one audit. This is the default mode.

## Read

- [audit-contract.md](../references/audit-contract.md)
- [check-workspace.md](../references/check-workspace.md)
- [finding-schema.md](../references/finding-schema.md)
- [severity.md](../references/severity.md)
- all specialized auditor instructions
- [readiness-audit.md](readiness-audit.md)

## Procedure

1. Reset the exact `.check/current` workspace with
   `reset_check_workspace.py --apply`.
2. Verify that `residualPaths` is empty before loading the Subject.
3. Freeze the current canonical artifact version and create one `runId`.
4. Dispatch these isolated auditors against the same frozen inputs:
   source, structure, content, coverage, question, solution, math, LaTeX,
   relation, provenance, rendering, and retrieval.
5. Let each dispatched auditor write only its own report under
   `.check/current/subagent-reports/`. A failed or unavailable auditor is
   recorded as skipped or failed, never silently omitted.
6. Run the Finding Merger to deduplicate observations, preserve related
   symptoms, and identify the earliest wrong rootLayer as the root cause.
7. Run the [readiness-audit](readiness-audit.md) aggregation against the
   merged findings and the Subject readiness contract.
8. Validate the final report with `validate_findings.py`.
9. Return severity counts, executed and skipped auditors, root causes, related
   findings, repair owners, and one final status: `PASS`, `PASS_WITH_WARNINGS`,
   `FAIL`, or `BLOCKED`.

## Gate

Full audit never repairs the Subject. A failed audit remains failed until learn
or the domain model produces a new artifact and check runs again.
