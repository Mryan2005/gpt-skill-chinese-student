---
name: sort
description: Use as the safe review-priority front door to rank existing knowledge cards by learning value and risk without changing canonical learning content or structure.
---

# Sort

`sort` decides what to review first. It reads the Subject, domain contract,
Learner Model, exam gaps, and current check findings to create an explainable
review-priority projection. It does not judge correctness or reorder the course.

## Non-negotiables

- Write only `sort-state.json` and local review-priority projections, orders,
  and queues.
- Do not change Source, cards, questions, solutions, relations, canonical
  Markdown, HTML, or canonical learner state.
- Do not change the chapter tree, parent-child relations, canonical card order,
  or card IDs.
- Split every score into nine traceable dimensions. Missing evidence is not zero.
- Give every queued card a reason and evidence. Mark weak signals as
  `insufficient-signal`.
- Use stable card IDs as the final tie-breaker.
- Use only state, exam reports, and check findings for the current artifact
  version.
- Do not repair check findings or write the projection into canonical content.
- Sorting is repeatable and reversible. It needs no destructive confirmation.

Read [sort-contract.md](references/sort-contract.md),
[priority-model.md](references/priority-model.md), [modes.md](references/modes.md),
and [build-review-priority.md](playbooks/build-review-priority.md).

## Routing

| User goal | Mode or playbook |
| --- | --- |
| Choose the next review items | `default`, using [build-review-priority.md](playbooks/build-review-priority.md) |
| Favor exam value and frequency | `exam` |
| Favor current weakness and recent errors | `weakness` |
| Favor error, confusion, and condition risk | `risk` |
| Favor prerequisites and dependency coverage | `prerequisite` |
| Create a short evening queue | `tonight`, using [tonight-queue.md](playbooks/tonight-queue.md) |

## State machine

~~~text
SORT_REQUEST
→ LOAD_CURRENT_ARTIFACT
→ COLLECT_VERSIONED_SIGNALS
→ SCORE_WITH_MODE
→ APPLY_STABLE_ORDER
→ WRITE_PRIORITY_PROJECTION
→ VALIDATE_RESULT
→ CLOSED
~~~

## Done gate

Write `sort.priority.v1` with the artifact version, mode, weights, nine
dimensions, reasons, evidence, stable rank, and structure-preservation flags.
Run `validate_priority.py`. Do not describe queue order as correctness or
mastery.
