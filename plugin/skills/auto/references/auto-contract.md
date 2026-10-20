# Auto orchestration contract

`auto` coordinates existing workflows. It owns only plans, execution state,
evidence, and acceptance reporting under `.auto/`. It never owns Source,
Derived knowledge, an Exam Result, official evidence, or Learner State.

## Plan and state

Each plan step names a public Skill invocation, dependencies, required inputs,
expected outputs, write boundary, authorization, acceptance criteria, and a
bounded failure policy. The plan may use the existing route registry and help
index, but it must not create a competing Skill registry.

`.auto/<runId>/plan.json` records the requested dependency graph. `state.json`
records step state, artifact hashes, executed validator commands, blockers,
attempts, and replanning history. Resume recalculates artifact hashes before
treating an old step as successful.

## Delegation protocol

1. Recheck dependencies, required artifacts, freshness, and authorization.
2. Load the delegated Skill's own contract and execute it through its normal
   workflow. `auto` must not reproduce its domain logic.
3. Register only real output files and run actual validator commands.
4. Compare validation evidence with the planned completion criteria.
5. Move to a dependent step, create a bounded repair route, or stop blocked.

The state engine rejects completion with no output artifact or no validator.
It does not pretend that a model's textual summary executed a Skill.

## Replanning

`fix` needs a fresh `check` report and is followed by an independent `check`.
If `fix` reports a stale check report, Auto marks that prerequisite pending,
reruns it, and only then retries the bounded fix step. Source gaps remain
blocked. Explicit correction routes to `amend`; missing
Missing Source remains blocked. Explicit correction routes to `amend`; missing
derived knowledge routes to `learn`; safe, bounded experience repair routes to
`heal`. Do not nest an unbounded loop or overwrite frozen evidence.

## Authorization

The original request authorizes ordinary operations only. `relearn` requires
its explicit destructive confirmation. `optimize apply` needs its own explicit
approval. Delegated contracts may impose stricter requirements.
