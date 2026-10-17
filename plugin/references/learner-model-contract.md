# Local Learner Model contract

The Local Learner Model is a private, local, evidence-based state layer. It
describes observed learning events and derived learning signals. It is not a
personality profile and it is not a second knowledge base.

## Layers

~~~text
Source
  original documents, questions, official answers, and official solutions

Derived Knowledge
  cards, relations, mappings, derived answers, solutions, and generated output

Learner
  observations, error model, explanation model, mastery, and sort state
~~~

The Learner layer must not write into Source, card provenance, public HTML,
canonical knowledge content, or the formal graph structure.

## Local storage

Use this default layout:

~~~text
.local/
└── learner/
    ├── global/
    │   ├── explanation-model.json
    │   └── preferences.json
    └── subjects/
        └── <subject-id>/
            ├── observations.jsonl
            ├── error-model.json
            ├── mastery.json
            ├── strategy-state.json
            └── sort-state.json
~~~

`.local/learner/` is persistent state. `.check/current/`, `.exam/current/`, and
`.fix/current/` are disposable workspaces. Their cleanup must never delete the
Learner layer.

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
about preference is evidence, but it is not the only evidence.

User corrections do not delete historical observations. They add counter-
evidence and reduce the confidence of the affected derived claim.

## Domain boundary

The core owns storage, evidence links, aggregation, confidence, recency, decay,
and state transitions. Each domain owns its error taxonomy and the meaning of
its explanation strategies. A math error such as `EVENT_REGION_ERROR` must not
be imposed on politics or English.

## Ownership

- `learn` reads the model before teaching and records new observations after a
  learning interaction.
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
observations, mastery, error reasons, explanation effectiveness, or sort scores
in public artifacts. A public-artifact leak is a blocker.
