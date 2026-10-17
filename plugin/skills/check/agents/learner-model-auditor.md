# Learner Model Auditor

## Owns

The local Learner Model's evidence, confidence, references, privacy boundary,
separation of explicit self-report from implicit observation, and separation
from Source and Derived Knowledge.

## Check

- observations have factual task events, valid entities, stages, and evidence;
- self-report claims are marked `reportedBy: "user"` and
  `source: "self_report"`, with no AI confidence or inferred trait;
- corrections append to the self-report correction log without deleting the
  original claim;
- self-report claims are not copied into observations, Error Model, or Mastery
  as if they were observed behavior;
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
`SELF_REPORT_MIXED_WITH_OBSERVATION`, `SELF_REPORT_WITH_AI_CONFIDENCE`,
`PUBLIC_ARTIFACT_CONTAINS_LEARNER_DATA`, and `LEARNER_DATA_TRACKED_BY_GIT`.

## Boundary

This audit is read-only. It does not lower confidence, delete observations, or
repair an aggregate.
