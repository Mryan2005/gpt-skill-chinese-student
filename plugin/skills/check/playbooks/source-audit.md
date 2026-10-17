# Source audit

## Use this playbook when

The user asks whether sources are complete, correctly classified, immutable,
or traceable.

## Dispatch

Run [source-auditor](../agents/source-auditor.md) and
[provenance-auditor](../agents/provenance-auditor.md) against the same frozen
Subject. Use the [audit contract](../references/audit-contract.md) and merge
their isolated reports before returning findings.

## Gate

Report missing, conflicting, unreadable, or misclassified source evidence with
concrete paths. Never delete, relabel, or restore a Source during the audit.
