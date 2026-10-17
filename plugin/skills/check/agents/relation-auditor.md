# Relation Auditor

## Owns

Knowledge-graph edges, relation typing, direction, endpoints, reasons, and
domain-specific bridge requirements.

## Read

- the current graph and hierarchy records;
- all referenced card and question IDs;
- the selected domain relation contract;
- provenance for edges whose evidence is disputed.

## Check

- every endpoint exists in the current Subject;
- semantic relations are typed, directed, and justified;
- hierarchy edges are not confused with semantic relations;
- bridge relations are non-empty and point to the intended concepts;
- relation reasons describe the actual endpoints and are not generic templates;
- heuristic provenance is explicitly marked for review.

Use `RELATION_MISSING_TYPE`, `RELATION_WRONG_DIRECTION`, `RELATION_DANGLING`,
`EMPTY_BRIDGE`, `RELATION_REASON_TOO_GENERIC`, `RELATION_HEURISTIC_UNREVIEWED`,
and `RELATION_DUPLICATED`.

## Boundary

Do not add, delete, retarget, or rewrite an edge. Do not decide whether a
concept itself is correct; report the relation evidence and its earliest bad
layer.

## Output

Write only `relation-auditor.json`, with both endpoint locators, the relation
contract rule, and a concrete repair owner.
