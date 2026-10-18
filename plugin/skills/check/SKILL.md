---
name: check
description: Use as the read-only multi-agent QA and audit front door for learning artifacts, including source integrity, knowledge structure, questions, relations, retrieval, rendering, and exam readiness.
---

# Check

`check` is the read-only QA and audit runner for the learning system. It
validates the Subject built by `learn` and the artifacts produced by a domain
model. It does not relearn, remap, or repair content.

## Non-negotiables

- Read only. Do not modify Markdown, HTML, records, learner state, or task state.
- Delete and recreate `.check/current/` before each audit. Verify that the
  workspace is empty before reading the current canonical state.
- Support every conclusion with an evidence path, entity ID, observed value,
  and expected value.
- Give every finding a code, severity, root layer, and repair owner.
- Distinguish `blocker`, `error`, `warning`, and `info`.
- "No errors found" does not mean that the content is correct. Report checks
  that did not run.
- Read domain contracts for subject-specific correctness. Do not copy
  mathematics rules into the common checker.
- Agents write only isolated reports. The Finding Merger combines reports but
  never repairs content.
- Agent capacity changes parallelism, not the required audit scope. Batch,
  share workers, or run the queue sequentially when capacity is low.
- After two consecutive agent-creation failures, stop spawning agents and move
  the remaining work to the fallback queue.
- Stop at the report after finding the root cause. Do not repair in `check`.

Read [audit-contract.md](references/audit-contract.md),
[execution-contract.md](references/execution-contract.md),
[check-workspace.md](references/check-workspace.md),
[finding-schema.md](references/finding-schema.md), and [severity.md](references/severity.md).

## Routing

| User goal | Playbook |
| --- | --- |
| Unclear scope or a complete audit | [full-audit.md](playbooks/full-audit.md) |
| Source, classification, or provenance problems | [source-audit.md](playbooks/source-audit.md) |
| Card, node, or hierarchy problems | [structure-audit.md](playbooks/structure-audit.md) |
| Incomplete source coverage | [coverage-audit.md](playbooks/coverage-audit.md) |
| Incomplete or shallow cards | [content-audit.md](playbooks/content-audit.md) |
| Misplaced, duplicated, or incomplete questions | [question-audit.md](playbooks/question-audit.md) |
| Conflicting answers, solutions, or provenance | [solution-audit.md](playbooks/solution-audit.md) |
| Mathematics semantics, theorems, or solutions | [math-audit.md](playbooks/math-audit.md) |
| LaTeX syntax or lost formula source | [latex-audit.md](playbooks/latex-audit.md) |
| Broken, untyped, or wrongly directed relations | [relation-audit.md](playbooks/relation-audit.md) |
| Broken pages, formulas, or interactions | [rendering-audit.md](playbooks/rendering-audit.md) |
| Knowledge points that search cannot find | [retrieval-audit.md](playbooks/retrieval-audit.md) |
| Review or exam readiness | [readiness-audit.md](playbooks/readiness-audit.md) |
| Learner evidence and privacy | [learner-model-audit.md](playbooks/learner-model-audit.md) |
| Fresh and explainable review priority | [sort-audit.md](playbooks/sort-audit.md) |

Choose the audit playbook from the user's goal, then load the Subject's domain
contract. The mathematics audit reads `study-math` schemas, validators, and readiness rules.

## State machine

~~~text
NEW_CHECK_REQUEST
→ CLEANUP_PREVIOUS_CHECK_RUN
→ WORKSPACE_VERIFIED_CLEAN
→ LOAD_CURRENT_CANONICAL_STATE
→ RUN_DETERMINISTIC_VALIDATORS
→ PLAN_AUDIT_EXECUTION
→ RUN_AUDIT_QUEUE → MERGE_FINDINGS → WRITE_FINDINGS → REPORT → CLOSED
~~~

## Done gate

Use the real canonical artifact, structured records, and rendered HTML. Run
`reset_check_workspace.py`, verify a clean workspace, and write findings with
severity, execution status, evidence paths, root layers, and repair owners.
The result must be `PASS`, `PASS_WITH_WARNINGS`, `FAIL`, or `BLOCKED`. Report
validation results only. Do not report repairs.
