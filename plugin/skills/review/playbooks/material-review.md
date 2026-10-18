# Material Review

Use this playbook when the goal is to turn reliable exam material into a
readable study resource. It is separate from Learner Review.

## Inputs

1. A closed `review.report.v2` produced from the immutable Exam Result.
2. Optional closed `exam-record.v1` details for official answers, solution
   status, page provenance, and first-pass measurement facts.
3. An exported canonical material catalog containing real card IDs, question
   records, source references, and typed relations. If the review report has
   only page provenance, prepare this catalog in the separate source-intake
   step with [extract_native_pdf_material.py](../scripts/extract_native_pdf_material.py)
   from native PDF text only; OCR is never a fallback.

Material Review itself never rereads the exam PDFs. If the supplied records contain
only PDF page provenance and no structured question text, report that as
`STRUCTURED_QUESTION_MISSING`; do not reconstruct a stem or option from a page
number.

## Procedure

1. Load the frozen review report and merge optional Exam Result details by
   immutable `questionId`.
2. Classify each question into an evidence tier: complete question analysis,
   question analysis without mapping, question analysis with a solution gap,
   card-backed analysis, answer conflict, source blocked, or structured input
   missing.
3. Count independent blocker flags and calculate unique-question and pairwise
   overlap counts. Do not add exclusive status counts as if they were always
   disjoint.
4. Build card-backed focus entries from canonical card content: core concept,
   key statements, boundaries, conditions, prerequisites, linked questions,
   source references, and recommended study actions.
5. Generate material learning tasks for `learn`. These tasks describe what to
   study; they do not write mastery or observations.
6. Generate an independent annotation overlay. Resolve a card anchor only when
   the card exists in the catalog. Keep a question anchor unresolved when the
   structured question record is absent.
7. Render deterministic Markdown and HTML with question-to-card links. The
   rendered view must show the scope of every frequency claim and every source
   gap.
8. Verify the Exam Result hash before and after. Validate the report and
   overlay. Re-running with identical inputs must produce identical output.

## Routing

- Mapping coverage: `check` identifies the defect, then `learn` rebuilds from
  reliable Source.
- Source or fixed-answer gaps: `check` identifies the boundary, then `learn`
  restores material intake without inventing evidence.
- Official-answer conflicts: `amend` and the applicable domain model.
- Learner mastery: not produced by this playbook. A later human closed-book
  attempt must create a new `attemptId` before Learner Review can update state.

## Outputs

`material-review-report.v2.json`, `material-review-annotations.json`,
`material-review.md`, and `material-review.html` are derived review artifacts.
They must state that the Exam Result, Source, canonical content, and Learner
Model were not mutated.
