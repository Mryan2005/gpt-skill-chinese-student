# Exam phase contract

The Exam Hit phase is a Question-by-Question Knowledge Coverage Test. Its only input
for the coverage judgment is the complete original exam and the actual content
of one frozen Subject snapshot.

## Statuses

- `HIT`: the current cards support a complete, correct solution through at
  least one verified route;
- `PARTIAL`: some required knowledge is supported, but a necessary condition,
  operation, relation, or reasoning step is missing;
- `MISS`: the current cards do not contain the key knowledge needed to solve the
  readable question;
- `UNRESOLVED`: the question or the evidence cannot be read or judged
  reliably. It is not counted as MISS.

Mapping failure is not knowledge failure. A question may be `HIT` with no
pre-existing question-to-card mapping when the supporting card content is
actually read and sufficient.

## Evidence contract

Every question must have:

- `requiredKnowledge` describing the actual operations, conditions, formulas,
  concepts, algorithms, or reasoning steps;
- `supportingCardIds` and `supportingCardContentRefs` when any current content
  supports it;
- content references with a card ID, a non-title field, an excerpt, and a
  content hash;
- `supportedReasoning`, `missingKnowledge`, `mappingIssues`, `evidenceRefs`,
  and confidence;
- an original PDF page reference.

The title of a card is never evidence. The model's private knowledge or a
specific answer memorized outside the snapshot is never evidence.

## Snapshot and ownership

The snapshot ID, artifact version, content hash, and card content are fixed for
the whole run. The run must report `snapshotMutated: false`,
`learnerModelMutation: false`, `examResultMutation: false`, and
`sourceMutation: false`. A new learning iteration produces a new snapshot and
a new hit run; it must not rewrite the old report.

## Aggregation

Compute counts from all question records after the full paper is processed:

```text
completeCoverageRate = HIT / totalQuestions
determinateCoverageRate = HIT / (HIT + PARTIAL + MISS)
```

The second rate excludes `UNRESOLVED` and must be labeled accordingly. Any
review priority or focus list is a derived result of observed question hits,
not an input to the judgment.
