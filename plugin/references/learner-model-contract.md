# Local Learner Model contract

The Local Learner Model is a private, local state layer with two separate
evidence streams: what the learner explicitly reports and what the system
observes during real learning. It is not a personality profile and it is not a
second knowledge base.

## Layers

~~~text
Source
  original documents, questions, official answers, and official solutions

Derived Knowledge
  cards, relations, mappings, derived answers, solutions, and generated output

Learner
  explicit self-report, implicit observations, error model, explanation model,
  mastery, and sort state
~~~

The Learner layer must not write into Source, card provenance, public HTML,
canonical knowledge content, or the formal graph structure.

## Local storage

Use this default layout:

~~~text
.local/
└── learner/
    ├── global/
    │   ├── profile/
    │   │   ├── self-report.json
    │   │   └── corrections.jsonl
    │   ├── explanation-model.json
    │   └── preferences.json
    └── subjects/
        └── <subject-id>/
            ├── profile/
            │   └── self-report.json
            ├── observations.jsonl
            ├── error-model.json
            ├── mastery.json
            ├── strategy-state.json
            └── sort-state.json
~~~

`.local/learner/` is persistent state. `.check/current/`, `.exam/current/`, and
`.fix/current/` are disposable workspaces. Their cleanup must never delete the
Learner layer.

## Explicit and implicit evidence

`profile` owns the explicit self-report layer. A self-report records a claim the
user chose to make about their own weakness, thinking habit, explanation
preference, or self-observation. Each claim must carry `reportedBy: "user"`
and `source: "self_report"`. It does not carry an AI confidence score.

Implicit observations belong in subject `observations.jsonl` and are produced
by actual learning, recall, explanation, or exam events. They may be aggregated
into Error Model, Explanation Model, Mastery, and strategy state, but they must
not be written into `profile/self-report.json`.

Corrections to a self-report append to `corrections.jsonl`. They do not delete
the original statement. Reports must show self-report and observation evidence
as separate sections when they agree or conflict.

## Evidence rules

An Observation records what happened: the task, stage, event, observed error,
strategy, hints, explanation patterns used, and outcome. It must not assert a
psychological label such as "visual learner" or "weak memory".

Error patterns aggregate observations. One observation cannot create a stable
high-confidence pattern. Repeated errors increase confidence. Independent
successes and long periods without recurrence decrease confidence through
`active`, `improving`, `dormant`, and `resolved` states.

Explanation effectiveness requires outcomes such as independent correctness,
follow-up count, hint count, self-recall, or transfer success. A user statement
about preference is explicit evidence, but it is not an implicit observation
and must not be silently converted into one.

User corrections do not delete historical observations. They add counter-
evidence and reduce the confidence of the affected derived claim.

## Domain boundary

The core owns storage, evidence links, aggregation, confidence, recency, decay,
and state transitions. Each domain owns its error taxonomy and the meaning of
its explanation strategies. A math error such as `EVENT_REGION_ERROR` must not
be imposed on politics or English.

## Ownership

- `learn` reads the model before teaching and records new observations after a
  learning interaction. It may use explicit self-reports to choose initial
  scaffolding, but it keeps that input separate from observations.
- `profile` appends explicit self-reports and user corrections only to the
  profile layer.
- `exam` may read the model before a snapshot is frozen. It must not expose
  learner hints during first-pass measurement. After grading, it records local
  observations and updates derived aggregates.
- `sort` reads the model and writes only `sort-state.json`.
- `check` audits the model and public-artifact boundaries without changing it.
- `fix` may repair schemas, indexes, references, aggregates, and sort state. It
  must not rewrite historical observations.
- `relearn` keeps global observations and increments a subject learning epoch;
  it rebuilds subject mastery, error aggregates, strategy state, and sort state.

## Privacy gate

Learner data is local-only by default. Do not commit, upload, publish, or embed
self-reports, observations, mastery, error reasons, explanation effectiveness,
or sort scores in public artifacts. A public-artifact leak is a blocker.
