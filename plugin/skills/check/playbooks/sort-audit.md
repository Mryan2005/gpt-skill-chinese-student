# Sort state audit

## Use this playbook when

The user asks whether personalized review order is current, explainable, and
private.

## Dispatch

Run [sort-state-auditor](../agents/sort-state-auditor.md) against the current
canonical artifact and local Learner Model.

## Gate

The projection must be local, version-matched, card-resolvable, and supported
by reasons and evidence. The audit does not change canonical order or sort
state.
