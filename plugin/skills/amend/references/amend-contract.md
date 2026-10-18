# Amend contract

`amend` consumes explicit user feedback about an existing learning artifact. It
does not treat the feedback as a new source document and does not require a
prior `check` report.

## Request and plan

Preserve the user's exact request in an amendment record with:

~~~json
{
  "source": "user_feedback",
  "request": "The ratio-test card omits the condition that rho = 1 is inconclusive.",
  "targets": ["card:ratio-test"]
}
~~~

Before writing, resolve the target and create an Amendment Plan. The plan must
name the affected layer, the entity ID, the action, the evidence used to locate
it, and any dependent artifacts that need a synchronized update. A user
statement is authorization to address the stated problem, not authorization to
change unrelated content.

## Writable layers

`amend` may change these layers when the feedback supports the change:

- Derived card content, explanations, examples, and recall prompts;
- derived answers and solutions;
- question-to-card mappings and typed relations;
- structured transcription or interpretation records derived from Source;
- generated Markdown, HTML, search indexes, and runtime artifacts;
- Learner Model derived aggregates and user-correction records.

Every change must point to the user feedback and pass targeted validation.

## Immutable Source and provenance

Keep original images, PDFs, questions, official answers, official solutions,
and Source Records unchanged.

For a transcription correction, keep the original transcription and append a
correction record, or preserve the old value in the record's provenance history:

~~~text
original image: unchanged
transcription: x^3 → x^2
source: user_feedback
reason: transcription_correction
~~~

For a disputed official answer, keep the official value and represent the
conflict explicitly:

~~~json
{
  "officialAnswer": "B",
  "userCorrection": "C",
  "derivedAnswer": "C",
  "answerStatus": "OFFICIAL_CONFLICT"
}
~~~

Do not silently turn a user correction into an official answer.

## Learner Model amendments

If the user corrects a claim about their own performance, preserve the original
Observation. Append user correction evidence and adjust only the derived Error
Model, Mastery, or strategy projection that depends on it. Keep the self-report
layer separate from implicit observations.

## Completion and escalation

Run only local validators that cover the changed targets. A successful local
validation is not a full audit. Write an append-only amendment history record at
`history/amendments.jsonl` when the Subject supports amendment history.

Use these terminal outcomes when needed:

- `NEEDS_CLARIFICATION`: the user feedback does not identify a reliable target
  or expected correction;
- `BLOCKED_BY_SOURCE`: required Source is missing, corrupted, or unreadable;
- `RELEARN_REQUIRED`: local repair would require deleting and rebuilding Derived;
- `UPDATE_REQUIRED`: the change is a schema or plugin migration.

After completion, recommend `$chinese-student:check` for full verification. Do
not run it automatically.
