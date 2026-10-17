# Fix from a check report

## Use this playbook when

The user invokes `fix` or asks to repair the latest check findings.

## Procedure

1. Reset the disposable `.fix/current` workspace.
2. Load the latest `check.finding.v1` report.
3. Verify the report against the current artifact version, hash, and schema.
4. Classify findings as deterministic, semantic, blocked, or escalated.
5. Build and validate a phased repair plan.
6. Analyze proposals with available workers. Fall back to shared or
   orchestrator execution when capacity is low.
7. Merge proposals, resolve conflicts, and apply writes in phase order.
8. Run targeted local validators.
9. Write a Fix Report and stop. Tell the user to run `check`.

## Gate

Do not ask for per-finding confirmation. Do not run a full check automatically.
Do not invoke `relearn` or `update`.
