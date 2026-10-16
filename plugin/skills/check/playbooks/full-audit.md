# Full audit

## Use this playbook when

Use it when the user asks to check a whole Subject or the scope is not narrow enough for one audit.

## Read

- [check-contract.md](../references/check-contract.md)
- [finding-schema.md](../references/finding-schema.md)
- [severity.md](../references/severity.md)
- all narrower audit playbooks

## Procedure

1. Freeze the Subject version and record every path that will be inspected.
2. Run source, knowledge, question, relation, retrieval, rendering, and readiness audits as read-only checks.
3. Deduplicate findings by code, layer, entity, and evidence.
4. Trace each blocker and error to its earliest wrong layer.
5. Validate the findings report with validate_findings.py.
6. Return counts by severity, executed and skipped checks, root causes, repair owners, and the final audit status.

## Gate

Full audit never repairs the Subject. A failed audit remains failed until learn or the domain model produces a new artifact and check runs again.
