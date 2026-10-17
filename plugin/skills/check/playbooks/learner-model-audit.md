# Learner Model audit

## Use this playbook when

The user asks whether local learner evidence, error patterns, explanation
strategies, mastery, or privacy boundaries are trustworthy.

## Dispatch

Run [learner-model-auditor](../agents/learner-model-auditor.md). Read the
Learner Model contract and the current local records. Do not read a public
artifact as learner evidence.

## Gate

One observation is not a stable learner claim. The audit reports stale,
unsupported, contradictory, or publicly exposed learner state without changing
the local model.
