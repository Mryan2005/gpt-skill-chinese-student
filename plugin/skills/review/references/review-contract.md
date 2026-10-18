# Review contract

`review` converts a closed Exam Result into evidence-backed learner feedback.
It does not rerun the exam, regrade, reread PDFs, remap the graph, audit Source,
or repair the learning artifact.

## Frozen input

The input must identify the `examRunId`, `subjectId`, frozen artifact version
and hash, immutable first-pass answers, `attemptId` values, grading evidence,
and question-level provenance. A missing or unfrozen first pass is an explicit
completeness gap. Do not rebuild it from an official solution.

The input must have `status: "CLOSED"`. Validate the result with
`validate_exam_result.py` before diagnosis. Review records
`examResultHashBefore` and `examResultHashAfter`; they must be equal.

Review also records a scope declaration. `reanswered`, `regraded`, `readPdf`,
`remappedGraph`, `auditedArtifact`, and `mutatedArtifact` must all be false.

## Question outcome and diagnosis

The Exam Result must distinguish attempt state, grading state, and artifact
state. `UNANSWERED_BY_LEARNER` is different from `NOT_ATTEMPTED`,
`BLOCKED_BY_SOURCE`, `BLOCKED_BY_MAPPING`, and `SKIPPED_BY_EXAM`.

Apply the Learner Attribution Gate only when all of these are true:

~~~text
FIRST_PASS_EXISTS
GRADING_RELIABLE
NO_UNRESOLVED_ANSWER_CONFLICT
NO_SOURCE_BLOCKER
NO_ARTIFACT_BLOCKER
~~~

Only an eligible question may produce an Observation, Mastery update, Error
Model update, or Sort signal. A blocked or ungraded question is never silently
converted into `MEMORY_FAILURE`, `RETRIEVAL_FAILURE`, or low mastery.

Each question has exactly one `observedOutcome`:

~~~text
correct
incorrect
partially_correct
unanswered
unreadable
ungraded
invalid
~~~

Only outcomes with sufficient evidence receive a confirmed error category. A
question with only a final answer may have a bounded hypothesis, but its
`errorStep` must be `null` unless the step is present in the record. Use
`diagnosticStatus` values `confirmed`, `hypothesis`, `unknown`, and `blocked`.

Error categories include:

~~~text
CONCEPT_MISUNDERSTANDING
KNOWLEDGE_MISSING
CONDITION_MISSED
METHOD_SELECTION_ERROR
REASONING_ERROR
EXECUTION_ERROR
READING_ERROR
CONNECTION_GAP
MEMORY_FAILURE
UNKNOWN
~~~

Every diagnosis has `questionId`, `attemptId`, `observedOutcome`,
`errorCategory`, `errorStep`, `evidenceRefs`, `hypotheses`, `confidence`, and
`diagnosticStatus`. A hypothesis is never serialized as a confirmed cause.

## Mastery separation

Use `primaryCardId`, `secondaryCardIds`, and typed relations to locate related
knowledge. Maintain separate assessments:

- Knowledge Mastery: the learner's grasp of a Card or concept;
- Question Mastery: the learner's grasp of a question, operation, or pattern.

Each assessment has a status from `unknown`, `needs_diagnosis`, `weak`,
`developing`, `proficient`, or `verified`; an evidence list; an assessment
reason; a timestamp; and a history entry. `verified` requires an independent,
scored, no-hint retest that meets the plan's coverage criteria.

Do not downgrade a whole Card because one operation failed. Do not upgrade a
Card because one question was correct.

## Completeness dimensions

Report these dimensions independently:

~~~text
examCompleteness
gradingCompleteness
diagnosticCompleteness
mappingCompleteness
masteryUpdateStatus
reviewStatus
~~~

Report attempted count, total count, scored count, ungraded count, unanswered
count, unreadable count, and invalid count. Never call `2/38` a mastery rate.

## Learning tasks

Each `learningTask` identifies what to learn, why it is needed, target cards or
questions, the problem to solve, the operation to use, dependencies, evidence,
and an acceptance criterion. `review` proposes tasks; `learn` executes them.

## Retest plans

Each `retestPlan` includes `targetCardIds`, `targetOperations`, `testMethod`,
`successCriteria`, `evidenceRequirements`, and `verificationStatus`. Prefer a
new question, a changed condition, a different wording, delayed recall, or an
unprompted solution. A repeated attempt after seeing the answer is not new
verification evidence.

## History and idempotence

Use immutable `attemptId` values to compare exams and retests. Compare scores
only when difficulty, coverage, conditions, and sample size are comparable.
Otherwise report `unknown` or `insufficient_sample`.

Every Learner Model write has an idempotency key:

~~~text
<examRunId>|<attemptId>|<diagnosticVersion>
~~~

Reprocessing the same report skips an existing key and preserves all historical
records. It never repeats counts or silently replaces a previous assessment.

## Routing

| Finding | Owner |
| --- | --- |
| Learner performance evidence | `review` → `sort` → `learn` |
| Official/source/solution conflict | `amend` |
| Question, mapping, formula, or renderer defect | `check`, `fix`, or `heal` |

`review` never modifies those other layers directly.

## Review workspace

Use `.review/current/` for input manifest, report, learner updates, routes, and
validation. Reset it before each run. Preserve `.exam/` and `.local/learner/`.
