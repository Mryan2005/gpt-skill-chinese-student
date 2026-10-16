# Grade an exam

## Use this playbook when

Use it when a frozen first-pass record exists and the user supplies an explanation PDF, answer key, or official grading source.

## Read

- [exam-contract.md](../references/exam-contract.md)
- [pdf-reading.md](../references/pdf-reading.md)
- [answer-record.md](../references/answer-record.md)
- [grading.md](../references/grading.md)
- [error-taxonomy.md](../references/error-taxonomy.md)

## Procedure

1. Load the existing record and verify that all first-pass answers are frozen.
2. Transition to SOLUTION_RELEASED only after the freeze check passes.
3. Read the original explanation PDF directly after the freeze. Preserve clipped, unreadable, and conflicting sections, and record original PDF pages.
4. Compare first_pass_answer with official_answer. Append grading evidence; do not rewrite the first pass.
5. Append post_review_answer only after the comparison.
6. Calculate Performance, Knowledge Coverage, Graph Effectiveness, and Error Profile.
7. Transition to GRADING, then route error analysis to analyze-errors.

## Gate

No official answer is allowed to enter a record whose first-pass answers are not frozen. Do not use OCR or an extracted transcript for the explanation PDF. A historical or inferred answer remains labeled and cannot become official evidence.
