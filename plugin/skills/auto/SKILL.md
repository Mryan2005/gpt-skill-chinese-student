---
name: auto
description: Use to orchestrate a compound learning request across existing Chinese Student workflows. It plans, delegates, validates real outputs, replans from evidence, and persists resumable state; it never becomes a second knowledge, exam, or repair owner.
---

# Auto

`auto` is the public orchestration front door. It understands compound learning
goals, creates a dependency-aware plan, delegates each ready step to an existing
public Skill, validates real artifacts, and persists state under `.auto/`.

## Non-negotiables

- Use [skill-registry.v1.json](../../references/skill-registry.v1.json) for
  Skill discovery, ownership, and canonical invocation. Do not invoke a
  `study-*` model or the internal Exam Hit phase as a public workflow.
- A plan is not execution. Never mark a step successful without actual output
  artifacts and validator evidence from the delegated Skill.
- Respect every delegated Skill's Source, provenance, Exam Result, Learner
  Model, workspace, authorization, and validation contracts.
- Never silently authorize `relearn` or `optimize apply`; do not bypass a stale
  `check` report before `fix`.
- Preserve frozen Exam Results. Never use OCR when delegating `exam` or turn an
  agent attempt into learner evidence.
- Keep repair loops bounded. Use `heal` for its existing maximum-five-round
  protocol; stop on unchanged findings, regression, insufficient evidence, or
  an unmet authorization.

## Modes

| Invocation | Behavior |
| --- | --- |
| `$chinese-student:auto` | Plan and execute ordinary authorized steps. |
| `$chinese-student:auto plan` | Write a plan only. |
| `$chinese-student:auto run` | Execute ready delegated steps and register real evidence. |
| `$chinese-student:auto resume` | Recheck artifact freshness and continue safely. |
| `$chinese-student:auto status` | Read current run state only. |
| `$chinese-student:auto explain` | Explain plan order, dependencies, authorization, and blockers. |

Read [auto-contract.md](references/auto-contract.md) before planning. Use
`scripts/auto.py` to persist and validate the run. The script is an evidence
gate, not a mock Skill executor: this Skill performs the actual delegation.

## Done gate

Report each requested outcome as satisfied, partial, blocked, or failed with
the actual delegated artifacts, validator evidence, authorization decisions,
and remaining recovery path. A narrative from a delegated agent is not proof.
