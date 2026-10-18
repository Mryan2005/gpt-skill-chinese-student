# Review contract

`review` consumes the structured output of `exam` and turns measured
performance into local learning feedback. It is not a second exam, a content
repairer, or a teaching session.

## Input contract

The Exam Result must identify:

- `examRunId`, `subjectId`, and the frozen artifact version and hash;
- immutable first-pass answer records;
- official, historical, or derived answer provenance;
- grading evidence, confidence, retrieval result, and cards used;
- the question-level error or source status.

Reject a stale, mutable, or incomplete result. Never use a later answer to
rewrite the first attempt.

## Diagnosis stages

Use the generic stages and domain-specific error taxonomy:

~~~text
RETRIEVAL
METHOD_SELECTION
CONDITION_CHECK
SETUP
EXECUTION
VERIFICATION
EXPRESSION
READING
MEMORY
TIME
SOURCE_ISSUE
~~~

The diagnosis must explain why the answer failed and cite grading or retrieval
evidence. Do not infer a stable weakness from one question. The observation may
be appended as a factual event; the Error Model decides whether repeated events
form a pattern.

## Three-way routing

| Diagnosis | Review action | Next owner |
| --- | --- | --- |
| Learner performance error | append Observation; update derived local aggregates | `sort` then `learn` |
| Content or provenance conflict | preserve Exam Result; create a repair request | `amend` |
| Question, mapping, renderer, or graph defect | preserve performance as non-diagnostic | `check`, `fix`, or `heal` |

Do not classify a question as a learner error when the question is incomplete,
the official answer conflicts with the source, or the mapped card cannot
support the tested operation.

## Learner Model writes

`review` may append to the Subject's `observations.jsonl` and update derived
Error Model, Mastery, Explanation Model, and strategy projections. Each write
must reference the Exam Result and question ID. Never overwrite an existing
Observation or change `Source`, canonical knowledge, or the Exam Result.

The remediation plan may include card IDs, question IDs, strategy codes, and
explanation modes. It is a plan for `learn`; it is not a content mutation.

## Completion

Write `review.report.v1`. Include `sort` and `learn` as next actions when the
review produced learner evidence. Include an `amend` request for content
conflicts and a `check`/`fix`/`heal` request for system defects. Run only local
Learner Model validation. A full artifact audit remains the user's explicit
`$chinese-student:check` action.
