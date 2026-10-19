# Heal contract

`heal` is a Learning Experience Optimizer. It asks a synthetic first-time
learner to learn from the artifact, captures learning friction, and lets an
independent Maintainer decide whether the friction justifies a repair.

## Round contract

Each repair round has the following stages:

~~~text
COLD_START / CHECK_BEFORE
→ LEARN / REFLECT
→ MAINTAINER_EVALUATE
→ REPAIR
→ OPTIMIZE (once, including NO_OP)
→ CHECK_AFTER / LOCAL_VALIDATE
~~~

The initial and final checks are read-only gates and do not consume repair
rounds. The next round creates a new novice context and reloads the current
user-facing artifact. The previous trace is comparison data, not current truth.

The novice must continue through the complete available learning path after
recording friction. It must not stop at the first problem or use outside
knowledge to fill a missing explanation.

## Role boundary

| Role | Permission | Responsibility |
| --- | --- | --- |
| Novice Learner | read-only | learn from the user-facing artifact and record a trace of understanding and friction |
| Maintainer | write-enabled | evaluate the trace against Source, domain contracts, schemas, and current artifacts; repair validated issues |
| Heal orchestrator | coordinates | reset isolated workspaces, create fresh novices, sequence rounds, compare progress, and report the result |

The Novice is not a checklist auditor. It does not inspect implementation
details, Source provenance, code, schemas, validators, old reports, or the real
Learner Model. The Maintainer must not blindly follow a novice suggestion.

The Maintainer chooses one decision for each friction finding:

- `ACCEPT`: the finding is valid and the proposed repair is safe;
- `REFINE`: the friction is valid, but the correct repair differs from the
  novice's suggestion;
- `REJECT`: the suggestion is not a valid content change, although the trace is
  retained as evidence for this run;
- `BLOCKED`: current Source or contracts cannot support a safe decision.

## Synthetic learner isolation

Novice traces are synthetic test data. They must never update:

~~~text
.local/learner/
learner_state.md
user profile or self-report
subject mastery
error model
explanation model
sort state
~~~

Store them only under `.heal/current/round-<n>/learner/`. Do not present a
synthetic observation as a user observation.

## Learning friction taxonomy

Use stable friction codes so that repeated novice runs can be compared:

~~~text
NOT_UNDERSTOOD
MISSING_PREREQUISITE
STEP_TOO_LARGE
NEEDS_DETAIL
TOO_VERBOSE
REDUNDANT
MERGE_CANDIDATE
SPLIT_NEEDED
ORDERING_PROBLEM
TERM_INTRODUCED_TOO_EARLY
TRIGGER_MISSING
CONDITION_MISSING
COMPARISON_MISSING
EXAMPLE_MISSING
EXAMPLE_NOT_REPRESENTATIVE
QUESTION_TOO_EARLY
RETRIEVAL_FRICTION
DEAD_END
COGNITIVE_OVERLOAD
~~~

Each friction record needs an entity or edge, the learner's attempted
understanding, a concrete reason, a needed improvement, a severity, and a
synthetic provenance marker. A trace must capture both friction and continued
progress after the friction.

## Maintainer repairs

The Maintainer may update Derived content, question mappings, typed relations,
generated artifacts, or validated learner-derived projections. It must preserve
Source, official answers, official solutions, historical observations, and
user-owned Learner Model data.

Use the existing `check` and `fix` contracts for technical validation or repair
when useful, and call the existing `optimize` contract once per round. A
technical `PASS` does not prove that the artifact is easy to learn, and a
novice complaint does not prove that cards should be merged.

## Convergence and stop conditions

Track at least:

- understanding coverage;
- learning dead ends;
- high- and medium-friction counts;
- unresolved `NOT_UNDERSTOOD` findings;
- missing prerequisites;
- redundancy, merge, and split candidates.

Stop with `HEALED` when high friction, dead ends, and unresolved
`NOT_UNDERSTOOD` findings are zero. Stop with `HEALED_WITH_WARNINGS` when only
optional medium-friction refinements remain. Stop with `STALLED` after two
rounds without meaningful pedagogical improvement. Stop with `BLOCKED` when
Source is missing, corrupted, unreadable, or insufficient for a safe repair.
Stop with `STOP_OPTIMIZATION_OSCILLATION` when opposite merge/split operations
target the same entities without new evidence. Stop with `MAX_ROUNDS_REACHED`
after five repair rounds.

`relearn` and `update` remain explicit escalation paths. Emit
`RELEARN_REQUIRED` or `UPDATE_REQUIRED` instead of invoking them.
