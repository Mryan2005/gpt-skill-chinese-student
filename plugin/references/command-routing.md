# Command routing contract

The machine-readable source of truth is
[`skill-registry.v1.json`](skill-registry.v1.json). This document explains how
the registry is used by a model or a route probe.

## Precedence

1. An explicit `$chinese-student:<skill>` identity wins.
2. A clear workflow goal wins over a generic subject word.
3. A subcommand or playbook is selected only when its evidence is present.
4. A domain phrase supplies a `domainModel` hint; it never turns an internal
   `study-*` model into a second public front door.
5. If two workflows have comparable evidence, return the candidates and ask
   one focused clarification. Do not guess.

The route probe is classification only. It never invokes a Skill, reads a
Subject, changes a workspace, or writes Learner State.

## Ownership boundaries

| User goal | Public owner | Important exclusion |
| --- | --- | --- |
| Build or update learning material | `learn` | Not audit, exam, review, sort, or destructive rebuild |
| Run a closed-book assessment | `exam` | Not post-exam teaching or artifact repair |
| Generate a practice paper | `practice` | Not grading or review |
| Review a frozen result or user submission | `review` | Not a new exam or graph audit |
| Audit an artifact | `check` | Read-only; never repair |
| Repair check findings | `fix` | Never invoke `relearn` implicitly |
| Improve a learning experience in bounded rounds | `heal` | No real Learner Model mutation |
| Optimize Derived graph structure | `optimize` | No Source or official-answer replacement |
| Generate a review projection | `sort` | No mastery or canonical-content mutation |
| Record explicit learner self-report | `profile` | No inferred observation or mastery |
| Apply explicit content feedback | `amend` | Requires user-directed evidence |
| Migrate versions and schemas | `update` | Not ordinary learning or rebuild |
| Rebuild Derived state | `relearn` | Explicit confirmation is mandatory |

`study-math`, `study-politics`, and
`study-exam-oriented-english` are internal domain models owned by `learn`.
The internal `exam-hit` phase is owned by `exam` and is never a standalone
public command.
