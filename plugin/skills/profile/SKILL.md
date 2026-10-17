---
name: profile
description: Use as the explicit self-report intake for learner weaknesses, thinking habits, explanation preferences, and self-observations. Keep self-reports separate from observed learning behavior and never infer personality traits.
---

# 中式学生：学习者自述入口

`profile` is the user's explicit input boundary for the Local Learner Model. It
records what the learner says about their own weaknesses, thinking habits,
explanation preferences, and self-observations. It is not an AI-generated
personality profile and it does not replace observed learning evidence.

## Input modes

- With no self-report, invite the learner to share current weak points, the
  step where they get stuck, their first move on an unfamiliar problem,
  explanations that work, and explanations they dislike.
- When the learner states a belief about themselves, append a claim to
  `.local/learner/global/profile/self-report.json` or to the selected Subject's
  profile when it is explicitly subject-specific.
- When the learner revises or withdraws an earlier statement, append a record to
  `.local/learner/global/profile/corrections.jsonl`; do not silently erase the
  original claim.

## Non-negotiables

- `profile` writes only the local explicit self-report layer. It never writes
  `observations.jsonl`, error aggregates, mastery, canonical knowledge, Source,
  public HTML, or Git-tracked artifacts.
- Every claim must be marked `reportedBy: "user"` and `source: "self_report"`.
- Do not add AI confidence, inferred traits, personality labels, or fixed
  learning-style labels to a self-report.
- Preserve the user's wording in `claim`; a controlled category may describe
  what the user explicitly said but must not turn it into a diagnosis.
- Self-reports and implicit observations must be shown separately. If they
  disagree, present both rather than silently choosing one.
- A self-report may guide initial scaffolding or review priority, but repeated
  observed behavior remains a separate evidence stream and is stronger for
  derived error patterns.

## Storage

~~~text
.local/
└── learner/
    ├── global/
    │   └── profile/
    │       ├── self-report.json
    │       └── corrections.jsonl
    └── subjects/
        └── <subject-id>/
            └── profile/
                └── self-report.json
~~~

Validate writes with `validate_learner_model.py self-report` or
`validate_learner_model.py correction`. `profile` may display the existing
observed model for comparison, but its durable output is the explicit
self-report layer.
