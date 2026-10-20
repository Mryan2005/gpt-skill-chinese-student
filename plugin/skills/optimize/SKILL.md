---
name: optimize
description: Use to analyze and safely optimize a Derived knowledge graph through evidence-backed duplicate, split, merge, and relation-migration plans. It does not audit source correctness, teach new material, or change Source.
---

# Optimize

`optimize` is the knowledge-graph optimization workflow. It works on Derived
cards, relations, mappings, and generated projections; Source, frozen Exam
Results, and Learner State remain protected.

## Modes

- `analyze` (default): read the current artifact and write a deterministic
  optimization plan. It does not mutate the artifact.
- `apply`: apply only a current, authorized plan. Exact duplicate aliases may
  be applied when their references can be migrated safely. Semantic merges,
  splits, and deletions are high risk and require explicit confirmation plus a
  complete migration plan; otherwise leave them recommended or blocked.
- `verify`: validate the migration, aliases, relation endpoints, mappings,
  learner-state references, provenance, and idempotence.

## Non-negotiables

- Preserve Source, frozen Exam Results, and Learner State. Record any
  referential effect instead of silently rewriting learner evidence.
- Every operation has a stable ID, evidence references, risk, decision, and
  target IDs. Never optimize from answer text alone.
- Keep related-but-distinct cards distinct. Do not merge on title similarity
  without semantic and provenance evidence.
- A high-risk merge, split, or deletion never runs without explicit user
  confirmation and a migration record.
- Re-running analysis after an applied plan must converge to no duplicate
  operation; repeated opposite merge/split proposals are a stability failure.
- `heal` calls this Skill once per round; it does not implement a second
  optimizer.

Read [optimize-contract.md](references/optimize-contract.md) and the relevant
playbook. Use `plan_optimize.py`, `apply_optimize.py`, and
`validate_optimize_report.py` for deterministic planning, guarded migration,
and verification.

## Output

Write an `optimize.report.v1` report with operation evidence, migration aliases
and remaps, preservation flags, confirmation state, and local validation. A
recommendation is not an applied change.
