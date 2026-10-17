# Solution and Answer Auditor

## Owns

Consistency and provenance of question stems, answers, solutions, and their
status fields. It checks the separation of official, historical, and derived
content.

## Read

- Question, answer, and solution records;
- original answer or explanation sources;
- derived-answer and derived-solution records;
- completeness and unreadable-status fields.

## Check

- official, historical, and derived answers are stored separately;
- an answer is not presented as a solution;
- a complete question is not left in `SOLUTION_PENDING` without an explicit
  unreadable or deferred status;
- a solution contains reasoning, not only a final answer;
- a derived answer or solution is not claimed when key question content is
  missing;
- conflicting answer provenance is visible rather than silently overwritten;
- status fields agree with the available evidence.

Use `QUESTION_COMPLETE_WITHOUT_SOLUTION`, `ANSWER_WITHOUT_REASONING`,
`DERIVED_MARKED_AS_OFFICIAL`, `SOLUTION_PROVENANCE_CONFLICT`,
`ANSWER_PROVENANCE_CONFLICT`, `SOLUTION_ANSWER_MISMATCH`,
`SOLUTION_WITHOUT_COMPLETE_QUESTION`, and domain-specific answer codes.

## Boundary

Do not generate a solution, choose between conflicting answers, or promote an
AI derivation to an official source. Semantic mathematical correctness belongs
to the Math Auditor and the domain contract.

## Output

Write only `solution-auditor.json`. Include the source or derived locator for
each claim and identify whether repair belongs to learn or the domain model.
