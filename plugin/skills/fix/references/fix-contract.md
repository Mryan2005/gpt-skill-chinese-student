# Fix contract

`fix` is the write-enabled half of the Diagnose and Repair boundary. It consumes
`check.finding.v1`; it does not replace `check` as the diagnostic authority.

## Input freshness

The input report must identify:

- `checkRunId`;
- the checked artifact version;
- the checked artifact hash;
- the checked schema version;
- the report generation time.

Before any write, compute the current values and compare all four identity
fields. A mismatch produces `STALE_CHECK_REPORT` and stops the run. Do not
repair a newer artifact with an older report.

## Automatic authorization

Calling `fix` authorizes automatic repair of every finding that stays within the
allowed mutation boundary. Do not ask for per-finding confirmation.

Allowed targets include Derived cards, mappings, derived answers and solutions,
relations, provenance links, LaTeX, canonical Markdown, HTML, indexes,
`learner_state`, local Learner Model schemas and derived aggregates, runtime
JavaScript, schema-compatible Derived data, and generated site artifacts.

## Immutable boundary

Never mutate original PDFs, images, original questions, official answers,
official solutions, Source quotes, or Source records. A source corruption or
missing source produces `BLOCKED_BY_SOURCE`.

`fix` is not `relearn`. If local repair is unsafe or the Derived layer is
systemically contaminated, return `RELEARN_RECOMMENDED`. Do not delete Derived
content or invoke `relearn`. If the issue is a version migration, return
`REQUIRES_UPDATE` instead.

## Repair order

Apply changes in dependency order:

1. Runtime and schema-compatible deterministic fields, including Learner Model
   indexes and aggregates;
2. provenance and source links;
3. card and question identities;
4. relations and mappings;
5. solutions and answers;
6. LaTeX and generated text;
7. Learner Model aggregates, Mastery, and sort projections;
8. renderer and generated artifacts.

Agents may analyze in parallel. Only the orchestrator writes, and it writes one
phase at a time after merging proposals and resolving path conflicts.

## Local validation

`fix` may run JSON parsing, schema checks, duplicate-ID checks, reference checks,
JavaScript syntax checks, HTML structure checks, and targeted markup checks. It
must report these as local validation. It must not present them as a complete
`chinese-student: check full-audit`, and it must not silently run one.

## Completion

The final report is `COMPLETE` when all input findings are resolved and local
validation passes. It is `PARTIAL` when progress was made but findings remain.
It is `BLOCKED` or `FAILED` when freshness, source, conflict, or validation
guards stop the run. Every report tells the user to run `chinese-student: check` next.
