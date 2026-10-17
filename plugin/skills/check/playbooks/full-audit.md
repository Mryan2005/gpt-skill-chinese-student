# Full audit

## Use this playbook when

Use it when the user asks to check a whole Subject or the scope is not narrow
enough for one audit. This is the default mode.

## Read

- [audit-contract.md](../references/audit-contract.md)
- [execution-contract.md](../references/execution-contract.md)
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
4. Run Level 0 deterministic validators without using agent capacity.
5. Plan the four auditor bundles with `plan_execution.py` and the currently
   available worker slots. Use parallel workers when possible, then batch,
   share one worker, or use the orchestrator fallback.
6. Stop creating new agents after two consecutive spawn failures. Continue the
   remaining queue through a shared worker or the orchestrator.
7. Let each completed auditor write only its own report under
   `.check/current/subagent-reports/`. Agent capacity failure is recorded in
   execution metadata, not as a skipped audit.
8. Run the Finding Merger to deduplicate observations, preserve related
   symptoms, and identify the earliest wrong rootLayer as the root cause.
9. Run the [readiness-audit](readiness-audit.md) aggregation against the
   merged findings and the Subject readiness contract.
10. Validate the final report with `validate_findings.py`.
11. Return severity counts, executed and blocked auditors, execution mode,
   root causes, related
   findings, repair owners, and one final status: `PASS`, `PASS_WITH_WARNINGS`,
   `FAIL`, or `BLOCKED`.

## Gate

Full audit never repairs the Subject. A failed audit remains failed until learn
or the domain model produces a new artifact and check runs again.
