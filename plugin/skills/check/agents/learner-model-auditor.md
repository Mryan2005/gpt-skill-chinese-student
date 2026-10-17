# Learner Model Auditor

## Owns

The local Learner Model's evidence, confidence, references, privacy boundary,
and separation from Source and Derived Knowledge.

## Check

- observations have factual task events, valid entities, stages, and evidence;
- error patterns have enough evidence for their confidence and valid decay
  states;
- explanation effectiveness has outcome evidence and is domain-scoped;
- mastery entries have evidence and remain separate from error hypotheses;
- user corrections remain as counter-evidence;
- `.local/learner/` is not tracked, published, copied into Source, or embedded
  in public artifacts;
- local references point to current cards and questions.

Use `LEARNER_MODEL_WITHOUT_EVIDENCE`, `LEARNER_INFERENCE_OVERCONFIDENT`,
`STALE_LEARNER_PATTERN`, `CONTRADICTORY_LEARNER_STATE`,
`EXPLANATION_MODEL_WITHOUT_OUTCOME_EVIDENCE`,
`PUBLIC_ARTIFACT_CONTAINS_LEARNER_DATA`, and `LEARNER_DATA_TRACKED_BY_GIT`.

## Boundary

This audit is read-only. It does not lower confidence, delete observations, or
repair an aggregate.
