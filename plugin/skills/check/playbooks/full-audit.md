# Full audit

## Use this playbook when

Use it when the user asks to check a whole Subject or the scope is not narrow enough for one audit.

## Read

- [check-contract.md](../references/check-contract.md)
- [check-workspace.md](../references/check-workspace.md)
- [finding-schema.md](../references/finding-schema.md)
- [severity.md](../references/severity.md)
- all narrower audit playbooks

## Procedure

1. Reset the exact .check/current workspace with reset_check_workspace.py --apply.
2. Verify that residualPaths is empty before loading the Subject.
3. Freeze the current canonical artifact version and record every path that will be inspected.
4. Run source, knowledge, question, relation, retrieval, rendering, and readiness audits as read-only checks.
5. Deduplicate findings by code, layer, entity, and evidence.
6. Trace each blocker and error to its earliest wrong layer.
7. Validate the findings report with validate_findings.py.
8. Return counts by severity, executed and skipped checks, root causes, repair owners, and the final audit status.

## Gate

Full audit never repairs the Subject. A failed audit remains failed until learn or the domain model produces a new artifact and check runs again.
