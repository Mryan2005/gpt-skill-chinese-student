# Learner-state fix

Repair schema-compatible `learner_state` projections, mastery bucket splits,
and stale generated review state when the source findings identify the exact
deterministic transformation. Do not infer mastery, erase learning history, or
turn an unresolved content defect into a mastered state.
