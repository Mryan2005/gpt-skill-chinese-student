# Learner Model audit

## Use this playbook when

The user asks whether local learner evidence, explicit self-reports, error
patterns, explanation strategies, mastery, or privacy boundaries are
trustworthy.

## Dispatch

Run [learner-model-auditor](../agents/learner-model-auditor.md). Read the
Learner Model contract and the current local records. Do not read a public
artifact as learner evidence.

Check the explicit self-report files separately from subject observations. A
user statement may guide scaffolding, but it must not be reported as a repeated
observed error or a derived personality claim.

## Gate

One observation is not a stable learner claim. The audit reports stale,
unsupported, contradictory, or publicly exposed learner state without changing
the local model.
