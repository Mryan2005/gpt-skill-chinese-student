# Sort State Auditor

## Owns

The local personal review projection derived from the Learner Model.

## Check

- every ranked card exists in the current Subject;
- artifact version and hash match the current canonical state;
- every priority has reasons and observation or mastery evidence;
- active error patterns influence relevant card ordering;
- resolved or dormant patterns do not remain permanently dominant;
- sort state is local-only and is not embedded in public HTML;
- relearn epochs invalidate stale sort state.

Use `SORT_REFERENCES_MISSING_CARD`, `SORT_STALE_LEARNER_STATE`,
`SORT_STALE_AFTER_RELEARN`, `SORT_WITHOUT_REASON`,
`SORT_PRIORITY_INCONSISTENT`, and `PUBLIC_ARTIFACT_CONTAINS_LEARNER_DATA`.

## Boundary

Do not reorder canonical cards or repair the projection during this audit.
